"""
A listener that raises used to end its suite: the exception escaped the suite's thread, the rest of the suite never ran
and its tests were left out of the summary and the reports, so a 4 test suite could finish as "2 tests, 100%". A
listener error is now recorded and the suite carries on; run() still fails at the end with TestListenerError. Tests a
suite never got to, because something else ended it early (a test calling sys.exit(), say), are reported as ignored.
Shared by the pytest and TJ test paths.
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile

from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.errors import TestListenerError
from test_junkie.listener import Listener
from test_junkie.runner import Runner

RAN = []


class BreaksOnB(Listener):

    def on_success(self, **kwargs):
        if kwargs["properties"]["jm"]["jto"].get_function_name() == "b":
            raise RuntimeError("listener bug on b")


class BreaksBeforeB(Listener):

    def on_in_progress(self, **kwargs):
        if kwargs["properties"]["jm"]["jto"].get_function_name() == "b":
            raise RuntimeError("listener bug before b")


@Suite(listener=BreaksOnB, parallelized=True)
class ListenerErrorMidSuite:

    @test()
    def a(self):
        RAN.append("a")

    @test()
    def b(self):
        RAN.append("b")

    @test()
    def c(self):
        RAN.append("c")

    @test()
    def d(self):
        RAN.append("d")


@Suite(listener=BreaksBeforeB, parallelized=True)
class ListenerErrorInProgressSuite:

    @test()
    def a(self):
        RAN.append("in_progress.a")

    @test()
    def b(self):
        RAN.append("in_progress.b")


@Suite(parallelized=True)
class ListenerErrorNeighbourSuite:

    @test()
    def x(self):
        RAN.append("x")

    @test()
    def y(self):
        RAN.append("y")


@Suite(parallelized=True)
class SuiteThreadDiesSuite:

    @test()
    def a(self):
        RAN.append("dies.a")

    @test()
    def b(self):
        sys.exit("test called sys.exit()")

    @test(parameters=[1, 2])
    def c(self, parameter):
        RAN.append("dies.c")


def _run(suites, expect, **kwargs):
    del RAN[:]
    out = io.StringIO()
    folder = tempfile.mkdtemp()
    report = os.path.join(folder, "report.json")
    try:
        with contextlib.redirect_stdout(out):
            try:
                Runner(suites, json_report=report).run(**kwargs)
                raise AssertionError("expected {}".format(expect.__name__))
            except expect:
                pass
        with open(report, encoding="utf-8") as doc:
            tests = {"{}.{}".format(suite["name"], unit["name"]): unit["status"]
                     for suite in json.load(doc)["suites"] for unit in suite["tests"]
                     if unit["parameter"] in (None, "None")}
        return out.getvalue(), tests
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def _listener_error_keeps_the_suite_running(**kwargs):
    out, tests = _run([ListenerErrorMidSuite, ListenerErrorNeighbourSuite], TestListenerError, **kwargs)
    assert sorted(r for r in RAN if len(r) == 1) == ["a", "b", "c", "d", "x", "y"], (RAN, out)
    for name in "abcd":
        assert tests["ListenerErrorMidSuite.{}".format(name)] == TestCategory.SUCCESS, tests
    assert "LISTENER" in out and "ListenerErrorMidSuite.b" in out and "on_success" in out, out
    assert "RuntimeError: listener bug on b" in out, out
    assert "1 listener call failed" in out, out
    assert "6 tests" in out, out


def listener_error_keeps_the_suite_running():
    _listener_error_keeps_the_suite_running()


def listener_error_keeps_the_suite_running_in_a_suite_thread():
    _listener_error_keeps_the_suite_running(suite_multithreading_limit=2)


def listener_error_keeps_the_suite_running_in_test_threads():
    _listener_error_keeps_the_suite_running(test_multithreading_limit=2)


def listener_error_before_a_test_still_runs_it():
    out, tests = _run([ListenerErrorInProgressSuite], TestListenerError)
    assert RAN == ["in_progress.a", "in_progress.b"], (RAN, out)
    assert tests["ListenerErrorInProgressSuite.b"] == TestCategory.SUCCESS, tests
    assert "on_in_progress" in out and "RuntimeError: listener bug before b" in out, out


def tests_a_dead_suite_never_ran_are_ignored():
    out, tests = _run([SuiteThreadDiesSuite], SystemExit, suite_multithreading_limit=2)
    assert "dies.c" not in RAN, RAN
    assert tests["SuiteThreadDiesSuite.a"] == TestCategory.SUCCESS, tests
    assert tests["SuiteThreadDiesSuite.b"] == TestCategory.IGNORE, tests
    assert "4 tests" in out, out  # a, b and both parameters of c - none of them left out of the summary
    assert out.count("SystemExit: test called sys.exit()") >= 1, out
    lines = [line.split() for line in out.splitlines() if line.split()[:1] == ["SuiteThreadDiesSuite"]
             and "[" not in line]
    assert lines and lines[-1][1] == "1" and lines[-1][4] == "3", out  # 1 passed, 3 ignored


CHECKS = [listener_error_keeps_the_suite_running, listener_error_keeps_the_suite_running_in_a_suite_thread,
          listener_error_keeps_the_suite_running_in_test_threads, listener_error_before_a_test_still_runs_it,
          tests_a_dead_suite_never_ran_are_ignored]
