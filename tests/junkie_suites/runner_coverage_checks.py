"""
Runner and ParallelProcessor paths that had no test: the run-wide exclusive gate, interrupts raised outside a test,
suites that end early, reruns over bad parameters, cancels during retries. Shared by both test paths:
tests/pytest/predeploy_tests/test_runner_coverage_checks.py and
tests/test_junkie/predeploy_tests/test_runner_coverage_checks.py
"""
import signal
import sys
import threading
import time

import test_junkie.runner as runner_module
from test_junkie.builder import Builder
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.errors import ConfigError, TestJunkieExecutionError
from test_junkie.listener import Listener
from test_junkie.parallels import ParallelProcessor
from test_junkie.rerun import Rerun
from test_junkie.retry import RetryPolicy
from test_junkie.runner import Runner

_GATE = ParallelProcessor._ParallelProcessor__GATE
_RUNNER = []  # the Runner of the check that's running, for tests that cancel their own run


def _reset_gate(saved=None):
    """
    Opens the gate. On the TJ path this check is itself a test of an outer run, which counts as one activity: the
    checks start from an open, idle gate and give the outer run its count back when they're done
    :param saved: DICT, what the gate held before the check
    """
    _GATE.update(saved or {"owner": None, "depth": 0, "active": 0})


def _gate_checked(check):
    """The check starts from an open, idle gate, and the gate is put back the way it was afterwards"""
    def wrapper():
        saved = dict(_GATE)
        _reset_gate()
        try:
            check()
        finally:
            _reset_gate(saved)
    wrapper.__name__ = check.__name__
    wrapper.__doc__ = check.__doc__
    return wrapper


def _in_thread(target, timeout=30):
    """Runs target() in a daemon thread so a hang fails the check instead of the whole session"""
    done = threading.Event()
    outcome = {}

    def go():
        try:
            outcome["value"] = target()
        except BaseException as error:  # a raised error is a result too
            outcome["error"] = error
        finally:
            done.set()

    threading.Thread(target=go, daemon=True).start()
    assert done.wait(timeout), "hung"
    return outcome


def _run(suites, **kwargs):
    """
    :return: (runner, error) - error is what run() raised, or None
    """
    runner = Runner(suites, quiet=True)
    _RUNNER[:] = [runner]
    try:
        runner.run(**kwargs)
        return runner, None
    except BaseException as error:  # SystemExit and KeyboardInterrupt are results here too
        return runner, error
    finally:
        _RUNNER[:] = []


def _status(suite, test_name, param=None, class_param=None):
    for test_object in Builder.get_execution_roster()[suite].get_test_objects():
        if test_object.get_function_name() == test_name:
            return test_object.get_status(param, class_param)
    raise AssertionError("no test {}".format(test_name))


def _statuses(suite, test_name):
    for test_object in Builder.get_execution_roster()[suite].get_test_objects():
        if test_object.get_function_name() == test_name:
            return [record["status"] for params in test_object.metrics.get_metrics().values()
                    for record in params.values()]
    raise AssertionError("no test {}".format(test_name))


# --- the exclusive gate (parallelized=False) ------------------------------------------------------------------------

def _hold_gate_in_thread():
    """
    Another thread takes the gate and keeps it until the returned release() is called
    :return: release
    """
    taken, release = threading.Event(), threading.Event()

    def holder():
        ParallelProcessor.acquire_exclusive()
        taken.set()
        release.wait(10)
        ParallelProcessor.release_exclusive()

    thread = threading.Thread(target=holder, daemon=True)
    thread.start()
    assert taken.wait(5), "the holder never got the gate"

    def stop():
        release.set()
        thread.join(5)
        assert not thread.is_alive(), "the holder never let go of the gate"
    return stop


def gate_activity_cancelled_while_another_thread_holds_it():
    """A test that is cancelled doesn't wait for the gate - it goes through to record CANCEL"""
    _reset_gate()
    stop = _hold_gate_in_thread()
    try:
        started = time.monotonic()
        with ParallelProcessor.activity(lambda: True):
            assert _GATE["active"] == 1, _GATE
        assert time.monotonic() - started < 0.2, "waited for the gate although cancelled"
        assert _GATE["active"] == 0, _GATE
    finally:
        stop()
        _reset_gate()


def gate_activity_waits_for_the_holder():
    """Not cancelled: the activity starts only once the holder lets go of the gate"""
    _reset_gate()
    stop = _hold_gate_in_thread()
    entered = threading.Event()
    try:
        def enter():
            with ParallelProcessor.activity(lambda: False):
                entered.set()
        thread = threading.Thread(target=enter, daemon=True)
        thread.start()
        assert not entered.wait(0.3), "an activity started while another thread held the gate"
        stop()
        assert entered.wait(5), "the activity never started after the gate opened"
        thread.join(5)
    finally:
        _reset_gate()


def gate_is_reentrant_for_its_holder():
    _reset_gate()
    me = threading.get_ident()
    try:
        ParallelProcessor.acquire_exclusive()
        ParallelProcessor.acquire_exclusive()  # a hook of the exclusive test takes it again
        assert _GATE["owner"] == me and _GATE["depth"] == 2, _GATE
        ParallelProcessor.release_exclusive()
        assert _GATE["owner"] == me and _GATE["depth"] == 1, "released after one of two acquires: {}".format(_GATE)
        ParallelProcessor.release_exclusive()
        assert _GATE["owner"] is None and _GATE["depth"] == 0, _GATE
    finally:
        _reset_gate()


def gate_release_by_another_thread_is_ignored():
    _reset_gate()
    stop = _hold_gate_in_thread()
    try:
        owner = _GATE["owner"]
        ParallelProcessor.release_exclusive()  # this thread doesn't hold it
        assert _GATE["owner"] == owner and _GATE["depth"] == 1, _GATE
    finally:
        stop()
        assert _GATE["owner"] is None, _GATE
        _reset_gate()


def gate_acquire_waits_for_another_holder():
    """A second exclusive test waits until the first one lets go, then holds the gate itself"""
    _reset_gate()
    stop = _hold_gate_in_thread()
    asks = []
    try:
        def cancel():
            asks.append(1)
            if len(asks) == 1:  # the holder lets go while this one waits
                threading.Thread(target=stop, daemon=True).start()
            return False
        outcome = _in_thread(lambda: (ParallelProcessor.acquire_exclusive(cancel), _GATE["owner"],
                                      threading.get_ident(), ParallelProcessor.release_exclusive())[1:3])
        assert "error" not in outcome, outcome
        owner, me = outcome["value"]
        assert owner == me, "the waiting thread didn't get the gate"
        assert asks, "never waited"
    finally:
        _reset_gate()


def gate_acquire_cancelled_while_another_thread_holds_it():
    """Cancelled: it stops waiting for the other holder (the run is over, nothing new starts)"""
    _reset_gate()
    stop = _hold_gate_in_thread()
    try:
        outcome = _in_thread(lambda: ParallelProcessor.acquire_exclusive(lambda: True), timeout=5)
        assert "error" not in outcome, outcome
    finally:
        stop()
        _reset_gate()


def gate_acquire_cancelled_while_activity_drains():
    """Cancelled while a test is still running: it stops waiting for it to finish"""
    _reset_gate()
    try:
        with ParallelProcessor.activity():
            started = time.monotonic()
            ParallelProcessor.acquire_exclusive(lambda: True)
            assert time.monotonic() - started < 0.2, "waited for running tests although cancelled"
            assert _GATE["owner"] == threading.get_ident() and _GATE["active"] == 1, _GATE
            ParallelProcessor.release_exclusive()
        assert _GATE == {"owner": None, "depth": 0, "active": 0}, _GATE
    finally:
        _reset_gate()


@Suite(parameters=[1, 2])
class ParallelTestsSuite:

    @test(parameters=[1, 2, 3])
    def slow(self, parameter, suite_parameter):
        time.sleep(0.05)


def wait_for_every_suites_tests():
    """wait_currently_active_tests_to_finish() with no suite waits for the test threads of every suite"""
    runner, error = _run([ParallelTestsSuite], test_multithreading_limit=3)
    assert error is None, error
    outcome = _in_thread(lambda: ParallelProcessor.wait_currently_active_tests_to_finish(None), timeout=10)
    assert "error" not in outcome, outcome
    assert _statuses(ParallelTestsSuite, "slow") == [TestCategory.SUCCESS] * 6


# --- Ctrl+C handling ------------------------------------------------------------------------------------------------

@Suite()
class PlainSuite:

    @test()
    def passes(self):
        pass


class _NoSignals(object):
    """signal module stand-in whose signal() fails the way it does on a thread or platform that can't take one"""
    SIGINT = signal.SIGINT
    default_int_handler = signal.default_int_handler

    def __init__(self):
        self.calls = 0

    @staticmethod
    def getsignal(signum):
        return signal.default_int_handler

    def signal(self, signum, handler):
        self.calls += 1
        raise ValueError("signal only works in main thread of the main interpreter")


def run_goes_on_when_the_ctrl_c_handler_cant_be_installed():
    if threading.current_thread() is not threading.main_thread():
        return  # the handler is only installed from the main thread
    before = signal.getsignal(signal.SIGINT)
    stand_in = _NoSignals()
    runner_module.signal = stand_in
    try:
        runner, error = _run([PlainSuite])
    finally:
        runner_module.signal = signal
    assert error is None, error
    assert stand_in.calls == 1, "never tried to install the handler"
    assert _status(PlainSuite, "passes") == TestCategory.SUCCESS
    assert signal.getsignal(signal.SIGINT) is before, "the real handler was changed"


class InterruptingListener(Listener):

    def on_in_progress(self, **kwargs):
        raise KeyboardInterrupt()  # a listener isn't a test: this ends the run as Ctrl+C would


@Suite(listener=InterruptingListener)
class InterruptInListenerSuite:
    runs = []

    @test()
    def first(self):
        InterruptInListenerSuite.runs.append("first")

    @test()
    def second(self):
        InterruptInListenerSuite.runs.append("second")


@Suite()
class AfterInterruptSuite:
    runs = []

    @test()
    def never(self):
        AfterInterruptSuite.runs.append("never")


def keyboard_interrupt_outside_a_test_cancels_the_run():
    """Raised by a listener, not by a test: nothing else starts, and run() raises it as a cancel by the user"""
    del InterruptInListenerSuite.runs[:], AfterInterruptSuite.runs[:]
    runner, error = _run([InterruptInListenerSuite, AfterInterruptSuite])
    assert isinstance(error, KeyboardInterrupt), repr(error)
    assert getattr(error, "tj_reported", False), "the console didn't report the cancel"
    assert InterruptInListenerSuite.runs == [] and AfterInterruptSuite.runs == [],         (InterruptInListenerSuite.runs, AfterInterruptSuite.runs)
    # the suite it came through and the one still queued are reported as cancelled, not left out of the reports
    for suite, name in ((InterruptInListenerSuite, "first"), (InterruptInListenerSuite, "second"),
                        (AfterInterruptSuite, "never")):
        assert _status(suite, name) == TestCategory.CANCEL, (suite.__name__, name, _status(suite, name))
    assert AfterInterruptSuite in [suite.get_class_object() for suite in runner.get_executed_suites()], \
        "the queued suite is missing from the results"


# --- several errors in one run --------------------------------------------------------------------------------------

@Suite()
class ExitsA:

    @test()
    def exits(self):
        sys.exit(3)


@Suite()
class ExitsB:

    @test()
    def exits(self):
        sys.exit(4)


def first_of_several_thread_errors_is_raised():
    runner, error = _run([ExitsA, ExitsB], suite_multithreading_limit=2)
    assert isinstance(error, SystemExit), repr(error)
    assert error.code in (3, 4), error.code
    assert _status(ExitsA, "exits") == TestCategory.IGNORE
    assert _status(ExitsB, "exits") == TestCategory.IGNORE


# --- a suite that ends early: tests it never got to -----------------------------------------------------------------

def _raising_parameters():
    raise ValueError("no parameters today")


def _not_a_list():
    return "not a list"


@Suite()
class EndsEarlySuite:

    @test()
    def exits(self):
        sys.exit(5)

    @test(skip=True)
    def skipped(self):
        pass

    @test()
    def not_in_rerun(self):
        pass

    @test(parameters=_raising_parameters)
    def raising_parameters(self, parameter):
        pass

    @test(parameters=_not_a_list)
    def wrong_parameters(self, parameter):
        pass

    @test()
    def plain(self):
        pass


def suite_that_ends_early_ignores_only_what_would_have_run():
    rerun = Rerun()
    for name in ("exits", "skipped", "raising_parameters", "wrong_parameters", "plain"):
        rerun.add("EndsEarlySuite", name)
    runner, error = _run([EndsEarlySuite, PlainSuite], suite_multithreading_limit=2, rerun=rerun)
    assert isinstance(error, SystemExit) and error.code == 5, repr(error)
    assert _status(EndsEarlySuite, "exits") == TestCategory.IGNORE
    assert _status(EndsEarlySuite, "plain") == TestCategory.IGNORE, "a test it never got to wasn't reported"
    assert _status(EndsEarlySuite, "skipped") is None, "a skipped test was reported as ignored"
    assert _status(EndsEarlySuite, "not_in_rerun") is None, "a test left out of the rerun was reported"
    assert _statuses(EndsEarlySuite, "raising_parameters") == [], "bad parameters got a made-up result"
    assert _statuses(EndsEarlySuite, "wrong_parameters") == []


def _broken_skip():
    raise RuntimeError("the skip check broke")


@Suite(skip=_broken_skip, parameters=_raising_parameters)
class BrokenSkipRaisingParametersSuite:

    @test()
    def runs_per_suite_parameter(self, suite_parameter):
        pass


@Suite(skip=_broken_skip, parameters=lambda: [])
class BrokenSkipEmptyParametersSuite:

    @test()
    def plain(self):
        pass


def broken_suite_skip_function_ignores_the_suites_tests():
    """
    The suite ends before its parameters are checked: they're read again to list its tests, and when they can't be
    used the tests are still reported once, as ignored with the error that ended the suite
    """
    for suite, name in ((BrokenSkipRaisingParametersSuite, "runs_per_suite_parameter"),
                        (BrokenSkipEmptyParametersSuite, "plain")):
        runner, error = _run([suite])
        # the intended message, naming the suite - it used to crash on a test-only method (get_function_module)
        assert isinstance(error, TestJunkieExecutionError), repr(error)
        assert "skip function '_broken_skip' in {}.{} raised".format(suite.__module__, suite.__name__) in str(error),             str(error)
        assert _statuses(suite, name) == [TestCategory.IGNORE], "{}: {}".format(name, _statuses(suite, name))
        assert _status(suite, name) == TestCategory.IGNORE


# --- reruns over bad parameters, ids= that don't give text ----------------------------------------------------------

@Suite()
class RerunBadParametersSuite:

    @test(parameters=_raising_parameters)
    def raising(self, parameter):
        pass

    @test(parameters=_not_a_list)
    def wrong(self, parameter):
        pass

    @test(parameters=lambda: [])
    def empty(self, parameter):
        pass

    @test()
    def left_out(self):
        pass


def rerun_still_reports_bad_parameters():
    rerun = Rerun().add("RerunBadParametersSuite", "raising").add("RerunBadParametersSuite", "wrong") \
        .add("RerunBadParametersSuite", "empty")
    runner, error = _run([RerunBadParametersSuite], rerun=rerun)
    assert error is None, error
    for name in ("raising", "wrong", "empty"):
        assert _statuses(RerunBadParametersSuite, name) == [TestCategory.IGNORE], \
            "{}: {}".format(name, _statuses(RerunBadParametersSuite, name))
    assert _status(RerunBadParametersSuite, "left_out") is None


@Suite()
class NumberIdsSuite:

    @test(parameters=[1, 2], ids=lambda parameter: parameter * 10)
    def numbered(self, parameter):
        pass


def ids_that_are_not_text_ignore_the_test():
    runner, error = _run([NumberIdsSuite])
    assert error is None, error
    for parameter in (1, 2):
        assert _status(NumberIdsSuite, "numbered", parameter) is None
    statuses = _statuses(NumberIdsSuite, "numbered")
    assert statuses == [TestCategory.IGNORE], statuses
    record = [record for params in Builder.get_execution_roster()[NumberIdsSuite].get_test_objects()[0]
              .metrics.get_metrics().values() for record in params.values()][0]
    assert "must give text" in str(record["exceptions"][-1]), record["exceptions"]


# --- cancels during retries -----------------------------------------------------------------------------------------

@Suite(retry=2)
class CancelledSuiteRetry:
    runs = []

    @test()
    def cancels_and_fails(self):
        CancelledSuiteRetry.runs.append(1)
        _RUNNER[0].cancel()
        assert False, "fails so the suite would be retried"


def cancel_stops_suite_retries():
    del CancelledSuiteRetry.runs[:]
    runner, error = _run([CancelledSuiteRetry])
    assert error is None, error
    assert len(CancelledSuiteRetry.runs) == 1, "the suite was retried after the run was cancelled"
    assert _status(CancelledSuiteRetry, "cancels_and_fails") == TestCategory.FAIL


class ResetOnce(RetryPolicy):
    attempts = 2
    reset = "class"


@Suite()
class CancelledResetSuite:
    runs = []

    @test(retry=ResetOnce)
    def held(self):
        CancelledResetSuite.runs.append(1)
        assert False, "fails, so its retry is held for a reset"

    @test()
    def cancels(self):
        _RUNNER[0].cancel()


def cancel_keeps_the_failure_of_a_held_reset_retry():
    del CancelledResetSuite.runs[:]
    runner, error = _run([CancelledResetSuite])
    assert error is None, error
    assert len(CancelledResetSuite.runs) == 1, "the held retry ran after the run was cancelled"
    assert _status(CancelledResetSuite, "held") == TestCategory.FAIL, _status(CancelledResetSuite, "held")


# --- the gate can't be taken: the conflicts reservation is given back ------------------------------------------------

@Suite()
class AloneSuite:

    @test(parallelized=False)
    def alone(self):
        pass


@Suite()
class AloneResetSuite:
    runs = []

    @test(parallelized=False, retry=ResetOnce)
    def alone(self):
        AloneResetSuite.runs.append(1)
        assert len(AloneResetSuite.runs) > 1, "fails the first time"


def _failing_gate(fail_on_call):
    """acquire_exclusive() that raises KeyboardInterrupt on its Nth call, and a log of release() calls"""
    original_acquire, original_release = ParallelProcessor.acquire_exclusive, ParallelProcessor.release
    calls, released = [], []

    def acquire(cancel=None):
        calls.append(1)
        if len(calls) == fail_on_call:
            raise KeyboardInterrupt()
        return original_acquire(cancel)

    def release(test_object):
        released.append(test_object.get_function_name())
        return original_release(test_object)

    def restore():
        ParallelProcessor.acquire_exclusive = staticmethod(original_acquire)
        ParallelProcessor.release = staticmethod(original_release)

    ParallelProcessor.acquire_exclusive = staticmethod(acquire)
    ParallelProcessor.release = staticmethod(release)
    return calls, released, restore


def reservation_given_back_when_the_gate_cant_be_taken():
    calls, released, restore = _failing_gate(fail_on_call=1)
    try:
        runner, error = _run([AloneSuite])
    finally:
        restore()
        _reset_gate()
    assert isinstance(error, KeyboardInterrupt), repr(error)
    assert calls == [1]
    assert released == ["alone"], released
    # it never ran (that would be success): the interrupt that stopped it is reported as a cancel
    assert _status(AloneSuite, "alone") == TestCategory.CANCEL, ("ran without the gate", _status(AloneSuite, "alone"))


def reservation_given_back_when_the_gate_cant_be_taken_for_a_held_retry():
    del AloneResetSuite.runs[:]
    calls, released, restore = _failing_gate(fail_on_call=2)
    try:
        runner, error = _run([AloneResetSuite])
    finally:
        restore()
        _reset_gate()
    assert isinstance(error, KeyboardInterrupt), repr(error)
    assert len(AloneResetSuite.runs) == 1, "the held retry ran without the gate"
    assert released == ["alone", "alone"], released
    assert _GATE["owner"] is None


# --- tag_config that can't be read ----------------------------------------------------------------------------------

class _UncomparableTag(object):
    """A tag that can't be compared with text - matching tags against tag_config then fails"""

    def __eq__(self, other):
        raise TypeError("can't compare")

    __hash__ = object.__hash__


@Suite()
class OddTagSuite:

    @test(tags=[_UncomparableTag()])
    def tagged(self):
        pass


def tags_that_cant_be_matched_are_a_config_error():
    runner, error = _run([OddTagSuite], tag_config={"skip_on_match_any": ["slow"]})
    assert isinstance(error, ConfigError), repr(error)
    assert "tag_config" in str(error), error
    assert _status(OddTagSuite, "tagged") is None, "ran although its tags couldn't be matched"


CHECKS = [
    _gate_checked(gate_activity_cancelled_while_another_thread_holds_it),
    _gate_checked(gate_activity_waits_for_the_holder),
    _gate_checked(gate_is_reentrant_for_its_holder),
    _gate_checked(gate_release_by_another_thread_is_ignored),
    _gate_checked(gate_acquire_waits_for_another_holder),
    _gate_checked(gate_acquire_cancelled_while_another_thread_holds_it),
    _gate_checked(gate_acquire_cancelled_while_activity_drains),
    _gate_checked(wait_for_every_suites_tests),
    _gate_checked(run_goes_on_when_the_ctrl_c_handler_cant_be_installed),
    _gate_checked(keyboard_interrupt_outside_a_test_cancels_the_run),
    _gate_checked(first_of_several_thread_errors_is_raised),
    _gate_checked(suite_that_ends_early_ignores_only_what_would_have_run),
    _gate_checked(broken_suite_skip_function_ignores_the_suites_tests),
    _gate_checked(rerun_still_reports_bad_parameters),
    _gate_checked(ids_that_are_not_text_ignore_the_test),
    _gate_checked(cancel_stops_suite_retries),
    _gate_checked(cancel_keeps_the_failure_of_a_held_reset_retry),
    _gate_checked(reservation_given_back_when_the_gate_cant_be_taken),
    _gate_checked(reservation_given_back_when_the_gate_cant_be_taken_for_a_held_retry),
    _gate_checked(tags_that_cant_be_matched_are_a_config_error),
]
