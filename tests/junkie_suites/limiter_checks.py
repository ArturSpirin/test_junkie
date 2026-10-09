"""
Limiter: truncation (exception message vs traceback, top/bottom/middle), run-wide throttling, @Suite(throttling=),
resource pools (uses=), ramp-up, and the run/CLI/config settings for all of it. Shared by the pytest and TJ test paths.

Before 0.9a8: EXCEPTION_MESSAGE_LIMIT did nothing on Python 3 (it set exception.message, which nothing reads),
TRACEBACK_LIMIT kept the start and cut off the failing line, and TEST_THROTTLING slept per suite thread, so two
parallel suites started tests twice as often as the limit said.
"""
import argparse
import json
import os
import shutil
import tempfile
import threading
import time

from test_junkie.cli.cli import CliUtils
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.errors import BadParameters
from test_junkie.listener import Listener
from test_junkie.objects import Limiter
from test_junkie.runner import Runner
from tests.junkie_suites import config_samples

EVENTS = []  # (name, time.monotonic(), tests running at that moment)
LISTENED = []
_RUNNING = [0]
_LOCK = threading.Lock()
RUNNER = [None]


def _work(name, seconds=0.0):
    with _LOCK:
        _RUNNING[0] += 1
        EVENTS.append((name, time.monotonic(), _RUNNING[0]))
    try:
        time.sleep(seconds)
    finally:
        with _LOCK:
            _RUNNING[0] -= 1


def _reset():
    del EVENTS[:]
    del LISTENED[:]
    _RUNNING[0] = 0


def _starts(prefix=""):
    return sorted(at for name, at, _ in EVENTS if name.startswith(prefix))


def _gaps(starts):
    return [round(b - a, 3) for a, b in zip(starts, starts[1:])]


class KeepsFullError(Listener):

    def on_failure(self, **kwargs):
        LISTENED.append(kwargs["exception"])


# ── fixtures ───────────────────────────────────────────────────────────────────────────────────────────────────

@Suite(listener=KeepsFullError)
class LongFailureSuite:

    @test()
    def long_message(self):
        assert False, "M" * 500

    @test(retry=2, retry_on=[AssertionError])
    def retried(self):
        assert False, "R" * 500


def _deep(depth):
    if depth == 0:
        raise AssertionError("the failing line")
    return _deep(depth - 1)


@Suite()
class DeepTracebackSuite:

    @test()
    def deep(self):
        _deep(40)


@Suite(parallelized=True)
class ThrottledA:

    @test()
    def a1(self):
        _work("t.a1")

    @test()
    def a2(self):
        _work("t.a2")


@Suite(parallelized=True)
class ThrottledB:

    @test()
    def b1(self):
        _work("t.b1")

    @test()
    def b2(self):
        _work("t.b2")


@Suite(parallelized=True, throttling=0)
class UnthrottledSuite:

    @test()
    def u1(self):
        _work("u.1")

    @test()
    def u2(self):
        _work("u.2")

    @test()
    def u3(self):
        _work("u.3")


@Suite(parallelized=True)
class GridSuite:

    @test(uses="grid", parameters=[1, 2, 3, 4, 5, 6], parallelized_parameters=True)
    def browser(self, parameter):
        _work("grid.{}".format(parameter), 0.2)

    @test(parameters=[1, 2, 3], parallelized_parameters=True)
    def api(self, parameter):
        _work("free.{}".format(parameter), 0.2)


@Suite(parallelized=True, uses="api")
class PacedSuite:

    @test()
    def p1(self):
        _work("paced.1")

    @test()
    def p2(self):
        _work("paced.2")

    @test()
    def p3(self):
        _work("paced.3")


@Suite()
class UnknownPoolSuite:

    @test(uses="nope")
    def t(self):
        _work("unknown")


@Suite(parallelized=True)
class RampSuite:

    @test(parameters=list(range(8)), parallelized_parameters=True)
    def t(self, parameter):
        _work("ramp.{}".format(parameter), 0.4)


@Suite(parallelized=True)
class CancelInPoolSuite:

    @test(uses="one", priority=1)
    def holder(self):
        _work("holder")
        RUNNER[0].cancel()
        time.sleep(0.5)

    @test(uses="one", priority=2)
    def waiter1(self):
        _work("waiter1")

    @test(uses="one", priority=3)
    def waiter2(self):
        _work("waiter2")


# ── helpers ────────────────────────────────────────────────────────────────────────────────────────────────────

def _run(suites, **kwargs):
    _reset()
    folder = tempfile.mkdtemp()
    report = os.path.join(folder, "report.json")
    try:
        runner = RUNNER[0] = Runner(suites, json_report=report)
        try:
            runner.run(quiet=True, **kwargs)
        except Exception as error:  # a failing test doesn't raise; only a run error does
            raise AssertionError("run raised {!r}".format(error))
        with open(report, encoding="utf-8") as doc:
            return json.load(doc)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def _units(report, suite, name):
    return [unit for s in report["suites"] if s["name"] == suite for unit in s["tests"] if unit["name"] == name]


def _failure(report, suite, name):
    unit = _units(report, suite, name)[0]
    text = json.dumps(unit)
    return unit, text


def _recorded(suite, name, what):
    """
    :param what: "tracebacks" or "exceptions"
    :return: what was recorded for the test's last run - what the console and HTML report show
    """
    from test_junkie.builder import Builder
    for test in Builder.get_execution_roster()[suite].get_test_objects():
        if test.get_function_name() == name:
            return test.metrics.get_metrics()["None"]["None"][what][-1]
    raise AssertionError("no test " + name)


def _traceback(suite, name):
    return _recorded(suite, name, "tracebacks")


# ── truncation ─────────────────────────────────────────────────────────────────────────────────────────────────

def truncate_modes():
    text = "HEAD" + "-" * 92 + "TAIL"  # 100 characters
    assert Limiter.truncate(text, 100) == text
    top = Limiter.truncate(text, 10, Limiter.TRUNCATE_TOP)
    assert top.endswith("TAIL") and "HEAD" not in top and "90 characters cut" in top, top
    bottom = Limiter.truncate(text, 10, Limiter.TRUNCATE_BOTTOM)
    assert bottom.startswith("HEAD") and "TAIL" not in bottom and "90 characters cut" in bottom, bottom
    middle = Limiter.truncate(text, 10, Limiter.TRUNCATE_MIDDLE)
    assert middle.startswith("HEAD") and middle.endswith("TAIL") and "90 characters cut" in middle, middle
    assert Limiter.truncate(text, 10) == middle  # middle is the default


def message_limit_applies_and_listeners_get_the_full_error():
    report = _run([LongFailureSuite], message_limit=40)
    unit, _ = _failure(report, "LongFailureSuite", "long_message")
    text = str(_recorded(LongFailureSuite, "long_message", "exceptions"))
    assert "M" * 41 not in text and "460 characters cut" in text, text[:600]
    assert unit["status"] == TestCategory.FAIL, unit["status"]  # still an AssertionError
    assert LISTENED and all(len(str(error)) == 500 for error in LISTENED), [len(str(e)) for e in LISTENED]


def truncated_exception_keeps_its_type_for_retry_on():
    report = _run([LongFailureSuite], message_limit=40)
    unit, _ = _failure(report, "LongFailureSuite", "retried")
    # retry_on=[AssertionError] matched the truncated copy: the test ran twice
    assert len([e for e in LISTENED if str(e).startswith("R")]) == 2, LISTENED


def traceback_middle_keeps_the_failing_line():
    _run([DeepTracebackSuite], traceback_limit=400)
    text = _traceback(DeepTracebackSuite, "deep")
    assert "Traceback" in text and "AssertionError: the failing line" in text and "characters cut" in text, text


def traceback_bottom_cuts_the_failing_line():
    _run([DeepTracebackSuite], traceback_limit=400, truncate="bottom")
    text = _traceback(DeepTracebackSuite, "deep")
    assert "Traceback" in text and "the failing line" not in text, text


def traceback_top_keeps_only_the_end():
    _run([DeepTracebackSuite], traceback_limit=400, truncate="top")
    text = _traceback(DeepTracebackSuite, "deep")
    assert "Traceback (most recent call last)" not in text and "the failing line" in text, text


def limits_off_keeps_everything():
    Limiter.ACTIVE = False
    try:
        _run([DeepTracebackSuite], traceback_limit=100, message_limit=5)
    finally:
        Limiter.ACTIVE = True
    text = _traceback(DeepTracebackSuite, "deep")
    assert "characters cut" not in text and "Traceback" in text and "the failing line" in text


# ── throttling ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_throttling_is_run_wide():
    _run([ThrottledA, ThrottledB], test_throttling=0.3, suite_multithreading_limit=2, test_multithreading_limit=4)
    starts = _starts("t.")
    assert len(starts) == 4, EVENTS
    # 0.9a7 slept per suite thread: two tests started together every 0.3 s
    assert all(gap >= 0.25 for gap in _gaps(starts)), _gaps(starts)


def suite_throttling_overrides_test_throttling():
    _run([UnthrottledSuite, ThrottledA], test_throttling=0.4, suite_multithreading_limit=2,
         test_multithreading_limit=4)
    unthrottled, throttled = _starts("u."), _starts("t.")
    assert len(unthrottled) == 3 and len(throttled) == 2, EVENTS
    assert unthrottled[-1] - unthrottled[0] < 0.2, _gaps(unthrottled)  # throttling=0: no wait between its tests
    assert _gaps(throttled)[0] >= 0.35, _gaps(throttled)  # the other suite still follows test_throttling


def run_limits_are_put_back_after_the_run():
    before = (Limiter.TEST_THROTTLING, Limiter.TRACEBACK_LIMIT, Limiter.TRACEBACK_TRUNCATE)
    _run([DeepTracebackSuite], test_throttling=0.1, traceback_limit=200, truncate="top")
    assert (Limiter.TEST_THROTTLING, Limiter.TRACEBACK_LIMIT, Limiter.TRACEBACK_TRUNCATE) == before


def bad_limits_are_rejected():
    for kwargs in ({"truncate": "side"}, {"test_throttling": -1}, {"traceback_limit": 1.5},
                   {"ramp_up": "fast"}):
        try:
            Runner([DeepTracebackSuite]).run(quiet=True, **kwargs)
        except BadParameters:
            continue
        raise AssertionError("{} was accepted".format(kwargs))


# ── pools ──────────────────────────────────────────────────────────────────────────────────────────────────────

def pool_caps_how_many_tests_hold_it():
    Limiter.pool("grid", max_concurrent=2)
    try:
        _run([GridSuite], test_multithreading_limit=9)
    finally:
        Limiter.remove_pools()
    grid = [name for name, _, _ in EVENTS if name.startswith("grid.")]
    assert len(grid) == 6, EVENTS
    # at most 2 browser tests at once; the api tests (no pool) weren't held back
    peak = _peak("grid.")
    assert peak == 2, peak
    assert _peak("") > 2, EVENTS


def _peak(prefix):
    """
    :return: INT, most tests with `prefix` running at once, from start/end times
    """
    spans = [(at, at + 0.2) for name, at, _ in EVENTS if name.startswith(prefix)]
    return max(sum(1 for s, e in spans if s <= at < e) for at, _ in spans)


def suite_uses_and_min_interval_pace_every_test():
    Limiter.pool("api", min_interval=0.3)
    try:
        _run([PacedSuite], test_multithreading_limit=3)
    finally:
        Limiter.remove_pools()
    starts = _starts("paced.")
    assert len(starts) == 3 and all(gap >= 0.25 for gap in _gaps(starts)), _gaps(starts)


def unknown_pool_is_rejected_before_anything_runs():
    _reset()
    try:
        Runner([UnknownPoolSuite]).run(quiet=True)
        raise AssertionError("uses=\"nope\" was accepted")
    except BadParameters as error:
        assert "nope" in str(error) and "Limiter.pool" in str(error), error
    assert not EVENTS, EVENTS


def bad_pool_definitions_are_rejected():
    for args, kwargs in ((("",), {}), (("x",), {"max_concurrent": 0}), (("x",), {"min_interval": -1}),
                         (("x",), {"max_concurrent": True})):
        try:
            Limiter.pool(*args, **kwargs)
        except BadParameters:
            continue
        finally:
            Limiter.remove_pools()
        raise AssertionError("Limiter.pool{} {} was accepted".format(args, kwargs))


def cancel_while_waiting_for_a_pool_cancels_the_waiters():
    Limiter.pool("one", max_concurrent=1)
    try:
        report = _run([CancelInPoolSuite], test_multithreading_limit=3)
    finally:
        Limiter.remove_pools()
    statuses = {name: _units(report, "CancelInPoolSuite", name)[0]["status"]
                for name in ("holder", "waiter1", "waiter2")}
    assert statuses["holder"] == TestCategory.SUCCESS, statuses
    assert statuses["waiter1"] == TestCategory.CANCEL and statuses["waiter2"] == TestCategory.CANCEL, statuses
    assert [name for name, _, _ in EVENTS] == ["holder"], EVENTS


# ── ramp-up ────────────────────────────────────────────────────────────────────────────────────────────────────

def ramp_up_grows_the_thread_limit():
    _run([RampSuite], ramp_up=1.2, test_multithreading_limit=4)
    first = min(at for _, at, _ in EVENTS)
    early = [running for _, at, running in EVENTS if at - first < 0.3]
    assert early and max(early) == 1, EVENTS  # one thread at the start
    assert max(running for _, _, running in EVENTS) >= 3, EVENTS  # and more once it ramped up


def no_ramp_up_starts_at_the_full_limit():
    _run([RampSuite], test_multithreading_limit=4)
    first = min(at for _, at, _ in EVENTS)
    assert max(running for _, at, running in EVENTS if at - first < 0.3) == 4, EVENTS


# ── CLI and config ─────────────────────────────────────────────────────────────────────────────────────────────

def cli_flags_parse():
    parser = argparse.ArgumentParser()
    CliUtils.add_options(parser, "run")
    args = parser.parse_args(["--test-throttling", "1.5", "--suite-throttling", "2", "--ramp-up", "10",
                              "--traceback-limit", "500", "--message-limit", "200", "--truncate", "top"])
    assert (args.test_throttling, args.suite_throttling, args.ramp_up) == (1.5, 2, 10), args
    assert (args.traceback_limit, args.message_limit, args.truncate) == (500, 200, "top"), args
    for bad in (["--truncate", "side"], ["--test-throttling", "-1"], ["--traceback-limit", "1.5"]):
        try:
            parser.parse_args(bad)
        except SystemExit:
            continue
        raise AssertionError("{} was accepted".format(bad))


def saved_limits_are_used():
    folder = tempfile.mkdtemp()
    try:
        path = config_samples.make_config(folder)
        config_samples.save(path, test_throttling=0.5, truncate="top", traceback_limit=1000)
        limits = config_samples.runtime_settings(path).limits
        assert limits == {"test_throttling": 0.5, "truncate": "top", "traceback_limit": 1000}, limits
    finally:
        shutil.rmtree(folder, ignore_errors=True)


CHECKS = [truncate_modes, message_limit_applies_and_listeners_get_the_full_error,
          truncated_exception_keeps_its_type_for_retry_on, traceback_middle_keeps_the_failing_line,
          traceback_bottom_cuts_the_failing_line, traceback_top_keeps_only_the_end, limits_off_keeps_everything,
          test_throttling_is_run_wide, suite_throttling_overrides_test_throttling,
          run_limits_are_put_back_after_the_run, bad_limits_are_rejected, pool_caps_how_many_tests_hold_it,
          suite_uses_and_min_interval_pace_every_test, unknown_pool_is_rejected_before_anything_runs,
          bad_pool_definitions_are_rejected, cancel_while_waiting_for_a_pool_cancels_the_waiters,
          ramp_up_grows_the_thread_limit, no_ramp_up_starts_at_the_full_limit, cli_flags_parse,
          saved_limits_are_used]
