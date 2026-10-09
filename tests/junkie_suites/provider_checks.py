"""
Parameter functions that raise (0.9a8, bug 3), shared by both test paths:
tests/pytest/predeploy_tests/on_test/test_provider_failures.py and
tests/test_junkie/predeploy_tests/test_provider_failures.py
"""
import os
import subprocess
import sys
import tempfile
import textwrap

from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.runner import Runner

CALLS = []
EVENTS = []


def source_down():
    CALLS.append("source_down")
    raise RuntimeError("source down")


def test_source_down():
    CALLS.append("test_source_down")
    raise RuntimeError("test source down")


class Events(Listener):

    def on_class_ignore(self, **kwargs):
        EVENTS.append(("class_ignore", kwargs["properties"]["jm"]["jso"].get_class_name()))

    def on_ignore(self, **kwargs):
        EVENTS.append(("ignore", kwargs["properties"]["jm"]["jto"].get_function_name()))


@Suite(listener=Events, priority=1)
class Before:
    @test()
    def runs(self):
        CALLS.append("Before.runs")


@Suite(listener=Events, parameters=source_down, priority=2)
class BadSuiteParameters:
    @test()
    def never(self, suite_parameter):
        CALLS.append("never")


@Suite(listener=Events, parameters=source_down, priority=3)
class SameBadProvider:
    @test()
    def never(self, suite_parameter):
        CALLS.append("never")


@Suite(listener=Events, priority=4)
class BadTestParameters:
    @test(parameters=test_source_down)
    def bad(self, parameter):
        CALLS.append("bad")

    @test()
    def sibling(self):
        CALLS.append("sibling")


@Suite(listener=Events, priority=5)
class After:
    @test()
    def runs(self):
        CALLS.append("After.runs")


SUITES = [Before, BadSuiteParameters, SameBadProvider, BadTestParameters, After]


def _run():
    del CALLS[:]
    del EVENTS[:]
    Runner(SUITES).run(quiet=True)  # must not raise


def _status(suite):
    return Builder.get_execution_roster().get(suite).get_status()


def _test(suite, name):
    for test_object in Builder.get_execution_roster().get(suite).get_test_objects():
        if test_object.get_function_name() == name:
            return test_object
    raise AssertionError(name)


def the_run_carries_on_past_a_raising_provider():
    _run()
    assert "Before.runs" in CALLS and "After.runs" in CALLS and "sibling" in CALLS, CALLS
    assert "never" not in CALLS and "bad" not in CALLS, CALLS


def a_suite_with_a_raising_provider_is_ignored():
    _run()
    assert _status(BadSuiteParameters) == TestCategory.IGNORE
    assert _status(SameBadProvider) == TestCategory.IGNORE
    assert ("class_ignore", "BadSuiteParameters") in EVENTS and ("class_ignore", "SameBadProvider") in EVENTS, EVENTS
    error = Builder.get_execution_roster().get(BadSuiteParameters).metrics.get_metrics()["initiation_error"]
    assert "source down" in str(error), error


def a_test_with_a_raising_provider_is_ignored_with_the_traceback():
    _run()
    data = _test(BadTestParameters, "bad").metrics.get_metrics()["None"]["None"]
    assert data["status"] == TestCategory.IGNORE
    assert "test source down" in str(data["exceptions"][-1])
    assert "RuntimeError: test source down" in data["tracebacks"][-1], data["tracebacks"][-1]
    assert ("ignore", "bad") in EVENTS, EVENTS
    assert _test(BadTestParameters, "sibling").metrics.get_metrics()["None"]["None"]["status"] == TestCategory.SUCCESS


def a_raising_provider_is_called_once_per_run():
    _run()
    assert CALLS.count("source_down") == 1, CALLS  # shared by two suites
    assert CALLS.count("test_source_down") == 1, CALLS
    _run()  # a new run calls it again: the source may be back
    assert CALLS.count("source_down") == 1, CALLS


def tj_run_still_fails():
    folder = tempfile.mkdtemp(prefix="tj_provider_")
    path = os.path.join(folder, "provider_suite.py")
    with open(path, "w", encoding="utf-8") as suite_file:
        suite_file.write(textwrap.dedent('''
            from test_junkie.decorators import Suite, test

            def broken():
                raise RuntimeError("source down")

            @Suite(parameters=broken)
            class Broken:
                @test()
                def never(self, suite_parameter):
                    pass

            @Suite()
            class Fine:
                @test()
                def ok(self):
                    pass
        '''))
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    env = dict(os.environ, PYTHONPATH=root + os.pathsep + os.environ.get("PYTHONPATH", ""))
    result = subprocess.run([sys.executable, "-m", "test_junkie", "run", "-s", path, "-q"], capture_output=True,
                            text=True, env=env, timeout=120)
    assert result.returncode == 1, (result.returncode, result.stdout[-2000:], result.stderr[-2000:])
    assert "Traceback (most recent call last)" not in result.stderr, result.stderr[-2000:]


CHECKS = [the_run_carries_on_past_a_raising_provider, a_suite_with_a_raising_provider_is_ignored,
          a_test_with_a_raising_provider_is_ignored_with_the_traceback, a_raising_provider_is_called_once_per_run,
          tj_run_still_fails]


if __name__ == "__main__":
    for check in CHECKS:
        try:
            check()
            print("PASS", check.__name__)
        except AssertionError as error:
            print("FAIL", check.__name__, str(error)[:400])
