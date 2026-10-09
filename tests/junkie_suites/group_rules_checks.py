"""
@beforeGroup / @afterGroup checks (0.9a8, bugs 5 and 7), shared by both test paths:
tests/pytest/predeploy_tests/before_class/test_group_rules_checks.py and
tests/test_junkie/predeploy_tests/test_group_rules_checks.py
"""
import threading
import time

from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test, GroupRules, beforeGroup, afterGroup
from test_junkie.listener import Listener
from test_junkie.rules import Rules
from test_junkie.runner import Runner

LOG = []
_LOCK = threading.Lock()


def _log(entry):
    with _LOCK:
        LOG.append((entry, time.monotonic()))


def _names():
    return [entry for entry, _ in LOG]


class GroupEvents(Listener):

    def on_before_group_failure(self, **kwargs):
        _log("event:before_group_failure")

    def on_before_group_error(self, **kwargs):
        _log("event:before_group_error")


# -- bug 5: one @beforeGroup shared by suites running in parallel ---------------------------------------------------

class ParallelGroupRules(Rules):

    @GroupRules()
    def group_rules(self):

        @beforeGroup([ParallelA, ParallelB, ParallelC])
        def set_up():
            _log("before:start")
            time.sleep(0.3)
            _log("before:end")

        @afterGroup([ParallelA, ParallelB, ParallelC])
        def tear_down():
            _log("after")


@Suite(rules=ParallelGroupRules)
class ParallelA:
    @test()
    def a(self):
        _log("test:a")


@Suite(rules=ParallelGroupRules)
class ParallelB:
    @test()
    def b(self):
        _log("test:b")


@Suite(rules=ParallelGroupRules)
class ParallelC:
    @test()
    def c(self):
        _log("test:c")


class FailingGroupRules(Rules):

    @GroupRules()
    def group_rules(self):

        @beforeGroup([FailingA, FailingB, FailingC])
        def set_up():
            _log("before:start")
            time.sleep(0.3)
            raise RuntimeError("group setup broke")


@Suite(rules=FailingGroupRules, listener=GroupEvents)
class FailingA:
    @test()
    def a(self):
        _log("test:a")


@Suite(rules=FailingGroupRules, listener=GroupEvents)
class FailingB:
    @test()
    def b(self):
        _log("test:b")


@Suite(rules=FailingGroupRules, listener=GroupEvents)
class FailingC:
    @test()
    def c(self):
        _log("test:c")


# -- bug 7: several @beforeGroup hooks on the same set of suites -----------------------------------------------------

class TwoHookRules(Rules):

    @GroupRules()
    def group_rules(self):

        @beforeGroup([TwoHooksA, TwoHooksB])
        def first():
            _log("before:first")

        @beforeGroup([TwoHooksA, TwoHooksB])
        def second():
            _log("before:second")

        @afterGroup([TwoHooksA, TwoHooksB])
        def after_first():
            _log("after:first")

        @afterGroup([TwoHooksA, TwoHooksB])
        def after_second():
            _log("after:second")


@Suite(rules=TwoHookRules)
class TwoHooksA:
    @test()
    def a(self):
        _log("test:a")


@Suite(rules=TwoHookRules)
class TwoHooksB:
    @test()
    def b(self):
        _log("test:b")


class FirstHookFailsRules(Rules):

    @GroupRules()
    def group_rules(self):

        @beforeGroup([FirstFailsA, FirstFailsB])
        def first():
            _log("before:first")
            raise RuntimeError("first hook broke")

        @beforeGroup([FirstFailsA, FirstFailsB])
        def second():
            _log("before:second")


@Suite(rules=FirstHookFailsRules)
class FirstFailsA:
    @test()
    def a(self):
        _log("test:a")


@Suite(rules=FirstHookFailsRules)
class FirstFailsB:
    @test()
    def b(self):
        _log("test:b")


def _run(suites, threads=1):
    del LOG[:]
    runner = Runner(suites)
    done = threading.Event()
    errors = []

    def go():
        try:
            runner.run(quiet=True, suite_multithreading_limit=threads)
        except Exception as error:  # a run-level error is a result too, but must not hang
            errors.append(error)
        finally:
            done.set()

    thread = threading.Thread(target=go, daemon=True)
    thread.start()
    assert done.wait(30), "the run hung"
    return runner, errors


def _statuses(suites):
    roster = Builder.get_execution_roster()
    return {suite.__name__: roster.get(suite).get_status() for suite in suites}


def before_group_runs_once_for_parallel_suites():
    _run([ParallelA, ParallelB, ParallelC], threads=3)
    names = _names()
    assert names.count("before:start") == 1, names
    assert names.count("after") == 1, names
    assert sorted(n for n in names if n.startswith("test:")) == ["test:a", "test:b", "test:c"], names


def tests_wait_until_before_group_has_finished():
    _run([ParallelA, ParallelB, ParallelC], threads=3)
    finished = next(t for name, t in LOG if name == "before:end")
    starts = [t for name, t in LOG if name.startswith("test:")]
    assert starts and all(start >= finished for start in starts), LOG


def failed_before_group_ignores_every_member_once():
    _run([FailingA, FailingB, FailingC], threads=3)
    names = _names()
    assert names.count("before:start") == 1, names
    assert not [n for n in names if n.startswith("test:")], names
    assert set(_statuses([FailingA, FailingB, FailingC]).values()) == {TestCategory.IGNORE}
    assert names.count("event:before_group_error") == 1, names


def failed_before_group_sequentially():
    _run([FailingA, FailingB, FailingC], threads=1)
    names = _names()
    assert names.count("before:start") == 1, names
    assert set(_statuses([FailingA, FailingB, FailingC]).values()) == {TestCategory.IGNORE}


def several_before_group_hooks_run_in_order():
    _, errors = _run([TwoHooksA, TwoHooksB])
    assert not errors, errors
    names = _names()
    assert names[:2] == ["before:first", "before:second"], names
    assert names.count("before:first") == 1 and names.count("before:second") == 1, names
    assert names[-2:] == ["after:first", "after:second"], names
    assert set(_statuses([TwoHooksA, TwoHooksB]).values()) == {TestCategory.SUCCESS}


def a_failing_hook_stops_the_rest_and_ignores_the_group():
    _, errors = _run([FirstFailsA, FirstFailsB], threads=2)
    assert not errors, errors
    names = _names()
    assert names == ["before:first"], names
    assert set(_statuses([FirstFailsA, FirstFailsB]).values()) == {TestCategory.IGNORE}


CHECKS = [before_group_runs_once_for_parallel_suites, tests_wait_until_before_group_has_finished,
          failed_before_group_ignores_every_member_once, failed_before_group_sequentially,
          several_before_group_hooks_run_in_order, a_failing_hook_stops_the_rest_and_ignores_the_group]


if __name__ == "__main__":
    for check in CHECKS:
        try:
            check()
            print("PASS", check.__name__)
        except AssertionError as error:
            print("FAIL", check.__name__, str(error)[:300])
