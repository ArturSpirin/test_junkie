"""
Checks for the run's console output (test_junkie/console.py) and for cancelling a run with Ctrl+C. Run by both test
paths: tests/pytest/predeploy_tests/test_console.py and tests/test_junkie/predeploy_tests/test_console.py.
Ctrl+C checks start a separate process - inside the TJ path the outer run owns the SIGINT handler
"""
import contextlib
import io
import logging
import os
import re
import subprocess
import sys
import textwrap
import threading

from test_junkie.console import parse_traceback
from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test, beforeClass, afterClass
from test_junkie.runner import Runner

ROOT = os.path.abspath(__file__).split(os.sep + "tests" + os.sep)[0]
FIRST = {"n": 0}
EVENTS = []
RUNNERS = []


@Suite()
class ConsoleMixedSuite:

    @test()
    def passes_quietly(self):
        print("PASS-MARK")

    @test(retry=3)
    def fails_differently_first(self):
        FIRST["n"] += 1
        print("FAIL-MARK")
        logging.getLogger("console.checks").warning("LOG-MARK")
        if FIRST["n"] == 1:
            raise TimeoutError("first run timed out")
        assert False, "expected 'Invalid password', got ''"


@Suite()
class ConsoleBeforeClassSuite:

    @beforeClass()
    def before_class(self):
        print("SETUP-MARK")
        raise ConnectionError("sandbox is not responding")

    @test()
    def first(self):
        pass

    @test()
    def second(self):
        pass


@Suite()
class ConsoleInterruptSuite:

    @test(priority=1)
    def runs(self):
        pass

    @test(priority=2)
    def presses_ctrl_c(self):
        raise KeyboardInterrupt

    @test(priority=3)
    def never_runs(self):
        pass

    @afterClass()
    def cleanup(self):
        EVENTS.append("afterClass")


@Suite()
class ConsoleCancelRetriesSuite:

    @test(retry=5)
    def cancels_then_fails(self):
        RUNNERS[0].cancel()
        assert False


def _run(suites, **kwargs):
    FIRST["n"] = 0
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        aggregator = Runner(suites).run(**kwargs)
    return aggregator, out.getvalue()


def tracebacks_print_as_lines():
    # every traceback in the summary used to print as one escaped line: "Traceback ...\n  File ..."
    _, out = _run([ConsoleMixedSuite])
    assert "\\n" not in out, out
    assert "  | AssertionError: expected 'Invalid password', got ''" in out, out


def retried_test_lists_every_run_and_groups_tracebacks():
    _, out = _run([ConsoleMixedSuite])
    assert "failed all 3 runs" in out, out
    assert "#1  ERROR" in out and "TimeoutError: first run timed out" in out, out
    assert "Run #1  traceback" in out and "Runs #2-#3  same traceback both times" in out, out
    assert out.count("AssertionError: expected") == 3, out  # twice in the runs list, once in the shared traceback


def output_is_shown_only_for_tests_that_did_not_pass():
    _, out = _run([ConsoleMixedSuite])
    assert "FAIL-MARK" in out and "PASS-MARK" not in out, out
    assert "  Output  run #3" in out, out
    assert "  Log  run #3" in out and "WARNING   console.checks  LOG-MARK" in out, out
    assert out.count("LOG-MARK") == 1, out  # captured, not also printed live


def no_capture_prints_output_live():
    _, out = _run([ConsoleMixedSuite], capture=False)
    assert "PASS-MARK" in out and "test output shown live" in out, out
    assert "  Output  " not in out, out


def quiet_run_prints_nothing():
    aggregator, out = _run([ConsoleMixedSuite], quiet=True)
    assert out == "", out
    assert aggregator.get_basic_report()["tests"][TestCategory.FAIL] == 1


def summary_table_and_verdict():
    _, out = _run([ConsoleMixedSuite])
    lines = out.splitlines()
    total = [line.split() for line in lines if line.split()[:1] == ["Total"] and "[" not in line]
    assert total and total[0][1:3] == ["1", "1"], out  # 1 passed, 1 failed
    assert "2 tests" in out and "[FAILED]" in out, out
    assert "exit code" not in out, out  # only tj run shows the exit code


def failed_before_class_is_one_entry():
    _, out = _run([ConsoleBeforeClassSuite])
    assert out.count("[IGNORED]") == 1, out
    assert "whole suite" in out and "@beforeClass failed" in out and "2 tests not run" in out, out
    assert "ConnectionError: sandbox is not responding" in out, out
    assert "  Output  @beforeClass" in out and "SETUP-MARK" in out, out


def per_test_prints_a_line_per_test():
    _, out = _run([ConsoleMixedSuite], per_test=True)
    assert "PASSED     passes_quietly" in out, out
    assert "FAILED     fails_differently_first" in out and "run 3/3" in out, out


def keyboard_interrupt_in_a_test_cancels_the_run():
    del EVENTS[:]
    out = io.StringIO()
    runner = Runner([ConsoleInterruptSuite])
    try:
        with contextlib.redirect_stdout(out):
            runner.run()
        raise AssertionError("expected KeyboardInterrupt")
    except KeyboardInterrupt as interrupt:
        assert getattr(interrupt, "tj_reported", False), "the console should have reported the cancel"
    report = {test.get_function_name(): test.get_status(None, None)
              for test in runner.get_executed_suites()[0].get_test_objects()}
    assert report == {"runs": TestCategory.SUCCESS, "presses_ctrl_c": TestCategory.CANCEL,
                      "never_runs": TestCategory.CANCEL}, report
    assert EVENTS == ["afterClass"], EVENTS  # cleanup still ran
    assert "[CANCELLED]" in out.getvalue() and "Summary" in out.getvalue(), out.getvalue()


def cancel_stops_retries():
    # cancel() used to apply only to tests that hadn't started - a running test kept retrying
    del RUNNERS[:]
    RUNNERS.append(Runner([ConsoleCancelRetriesSuite]))
    with contextlib.redirect_stdout(io.StringIO()):
        RUNNERS[0].run()
    test_object = RUNNERS[0].get_executed_suites()[0].get_test_objects()[0]
    statuses = test_object.metrics.get_metrics()["None"]["None"]["statuses"]
    assert statuses == [TestCategory.FAIL], statuses


def parse_traceback_keeps_the_users_frames():
    try:
        try:
            raise KeyError("first")
        except KeyError:
            raise ValueError("second")
    except ValueError:
        import traceback
        trace = traceback.format_exc()
    frames, exception = parse_traceback(trace)
    assert exception == ["ValueError: second"], exception  # only the last exception of the chain
    assert frames and frames[-1][2] == "parse_traceback_keeps_the_users_frames", frames
    wrapped = 'Traceback (most recent call last):\n  File "{}", line 1, in run\n    x()\nValueError: boom\n'.format(
        os.path.join(ROOT, "test_junkie", "runner.py"))
    assert parse_traceback(wrapped) == ([], ["ValueError: boom"])  # Test Junkie's own frames are left out


class _FakeTTY(io.StringIO):

    def isatty(self):
        return True


def live_bars_redraw_in_place():
    tty = _FakeTTY()
    previous = sys.stdout
    sys.stdout = tty
    try:
        Runner([ConsoleBeforeClassSuite]).run()
    finally:
        sys.stdout = previous
    out = tty.getvalue()
    assert "F\x1b[J" in out, repr(out[:400])  # cursor up + clear: the live block is redrawn in place
    plain = re.sub(r"\x1b\[[0-9;]*m", "", out)
    assert "Total" in plain and "Problems 1" in plain, repr(plain[-400:])


_INTERRUPTED = textwrap.dedent("""
    import signal, sys, threading, time
    sys.path.insert(0, {root!r})
    from test_junkie.decorators import Suite, test, afterClass
    from test_junkie.runner import Runner

    @Suite()
    class SlowSuite:
        @test(parameters=list(range(8)), parallelized_parameters=True)
        def step(self, parameter):
            time.sleep(0.3 if parameter < 7 else 4)

        @afterClass()
        def cleanup(self):
            print("AFTER-CLASS-RAN")

    for at in {times!r}:
        threading.Timer(at, lambda: signal.raise_signal(signal.SIGINT)).start()
    try:
        Runner([SlowSuite]).run(test_multithreading_limit={threads})
    except KeyboardInterrupt as interrupt:
        print("RAISED", getattr(interrupt, "tj_reported", False))
""")


def _interrupted(times, threads):
    script = _INTERRUPTED.format(root=ROOT, times=times, threads=threads)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", TJ_NO_LIVE="1", NO_COLOR="1")  # CI turns colors on
    process = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, encoding="utf-8",
                             env=env, timeout=60)
    return process.returncode, process.stdout + process.stderr


def ctrl_c_cancels_a_threaded_run():
    code, out = _interrupted([0.5], threads=3)
    assert code == 0 and "RAISED True" in out, out
    assert "CANCELLING" in out and "Waiting for 3 tests" in out and "Press Ctrl+C again" in out, out
    assert out.count("  finished SlowSuite.step") == 3, out  # only the tests that were running
    assert "AFTER-CLASS-RAN" not in out, out  # cleanup ran, but its output is captured, not printed
    assert "CANCELLED" in out and "Summary" in out, out


def ctrl_c_interrupts_a_sequential_test():
    code, out = _interrupted([0.5], threads=1)
    assert code == 0 and "RAISED True" in out, out
    lines = [line.split() for line in out.splitlines() if line.split()[:1] == ["Total"] and "[" not in line]
    assert lines and lines[0][1] == "1" and lines[0][6] == "7", out  # 1 passed, the rest (incl. the running one) cancelled


def second_ctrl_c_stops_immediately():
    code, out = _interrupted([1.0, 1.5], threads=8)  # step[7] is still running at 1.5s
    assert code == 130, (code, out)
    assert "STOPPED" in out and "still running" in out, out
    assert "Summary" not in out, out


CHECKS = [tracebacks_print_as_lines, retried_test_lists_every_run_and_groups_tracebacks,
          output_is_shown_only_for_tests_that_did_not_pass, no_capture_prints_output_live, quiet_run_prints_nothing,
          summary_table_and_verdict, failed_before_class_is_one_entry, per_test_prints_a_line_per_test,
          keyboard_interrupt_in_a_test_cancels_the_run, cancel_stops_retries, parse_traceback_keeps_the_users_frames,
          live_bars_redraw_in_place, ctrl_c_cancels_a_threaded_run, ctrl_c_interrupts_a_sequential_test,
          second_ctrl_c_stops_immediately]
