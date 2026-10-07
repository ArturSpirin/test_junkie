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


@Suite()
class ConsoleSlowSuite:

    @test(parameters=[1, 2, 3])
    def takes_a_while(self, parameter):
        import time
        time.sleep(0.35)


SLOW_SUITE_SOURCE = """
import time
from test_junkie.decorators import Suite, test


@Suite()
class SlowMSuite:

    @test(parameters=[1, 2, 3])
    def takes_a_while(self, parameter):
        time.sleep(0.35)
"""


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


# ── tj run -m: the resources chart ──────────────────────────────────────────────────────────────────────────────

def _plain_style(text, *names):
    return str(text)


def _chart(**overrides):
    from test_junkie.console import resource_chart
    start = 1000.0
    samples = [(start + i * 0.25, 20 + (i % 8) * 10, 50 + i * 0.5) for i in range(41)]  # 10s, CPU peaks at 90%
    tests = [(start + i, start + i + 0.5, "success") for i in range(8)] + [
        (start + 8.0, start + 8.4, "fail"), (start + 8.1, start + 8.4, "error"), (None, start + 8.4, "skip"),
        (None, start + 8.4, "ignore"), (None, start + 8.4, "ignore")]  # 5 results in the same column
    suites = [("LoginSuite", start, start + 6.0), ("CheckoutSuite", start + 6.0, start + 10.0)]
    kwargs = dict(style=_plain_style, samples=samples, start=start, end=start + 10.0, tests=tests, suites=suites,
                  width=60)
    kwargs.update(overrides)
    return resource_chart(**kwargs)


def resource_chart_sequential_layout():
    lines = _chart()
    text = "\n".join(lines)
    assert lines[0].startswith("Resources CPU and memory, whole machine"), text
    assert "CPU     avg 54% · peak 90% at 1.75s · during LoginSuite" in text, text
    assert "Memory  avg 60% · peak 70% at 10s" in text, text
    plot = [line for line in lines if "┤" in line or "┼" in line]
    assert len(plot) == 9 and all(len(line) == len(plot[0]) for line in plot), text  # 8 rows + the 0% axis, aligned
    assert plot[0].startswith("   100% ┤") and plot[-1].startswith("     0% ┼"), text
    first = next(i for i, line in enumerate(lines) if line.startswith("   tests "))
    dots = lines[first:first + 3]
    assert sum(line.count("●") for line in dots) == 8 + 2 and "+" in dots[-1], text  # 3 rows, then "+" for the rest
    assert "running" not in text and "tests running at once" not in text, text  # only for threaded runs
    suites = [line for line in lines if line.startswith("  suites ")]
    assert len(suites) == 1 and "├Login" in suites[0] and "├Checkout" in suites[0], text  # sequential: one lane
    assert lines[-3].rstrip().endswith("10s"), text  # the time axis ends with the run time


def resource_chart_threaded_lanes_and_running_row():
    start = 1000.0
    suites = [("LoginSuite", start, start + 9.0), ("CheckoutSuite", start, start + 4.0),
              ("SearchSuite", start + 4.0, start + 8.0)]  # Search waits for Checkout's lane
    tests = [(start + i * 0.5, start + i * 0.5 + 2.0, "success") for i in range(12)]
    lines = _chart(suites=suites, tests=tests, parallel=True, test_threads=4)
    text = "\n".join(lines)
    assert "tests running at once, out of 4 test threads" in text, text
    running = [line for line in lines if line.startswith("  running")]
    assert running and running[0].rstrip().endswith("peak 4 of 4"), text
    lanes = [line for line in lines if "├" in line]
    assert len(lanes) == 2 and "├Login" in lanes[0] and "├Checkout" in lanes[1] and "├Search" in lanes[1], text


def resource_chart_too_short_to_sample():
    lines = _chart(samples=[(1000.1, 5.0, 40.0)], end=1000.2)
    assert "too short to sample" in lines[-1], lines


def run_with_monitor_resources_prints_the_chart():
    from test_junkie.metrics import ResourceMonitor
    seen = []
    original = ResourceMonitor.shutdown

    def keep(self):
        original(self)
        seen.append(list(self.samples))
    ResourceMonitor.shutdown = keep
    try:
        _, out = _run([ConsoleSlowSuite], monitor_resources=True)
    finally:
        ResourceMonitor.shutdown = original
    assert "resource monitoring" in out and "Resources CPU and memory, whole machine" in out, out
    assert out.index("Summary") < out.index("Resources") < out.index("[PASSED]"), out  # after the summary
    tests = [line for line in out.splitlines() if line.startswith("   tests ")]
    assert tests and tests[0].count("o") >= 1, out  # ASCII "o" dots: StringIO can't take the unicode ones
    assert seen and len(seen[0]) >= 3 and all(0 <= cpu <= 100 and 0 <= mem <= 100 for _, cpu, mem in seen[0]), seen
    out.encode("ascii")  # the ASCII stand-ins cover every chart character
    _, out = _run([ConsoleSlowSuite], monitor_resources=True, quiet=True)
    assert out == "", out


def tj_run_dash_m_reaches_the_run():
    # tj run -m used to be dropped by the CLI: nothing was monitored unless -m was saved with tj config update
    from tests.junkie_suites.cli_checks import run_cli, _write
    code, out = run_cli("run", "-s", _write(SLOW_SUITE_SOURCE, "slow_m_suite.py"), "-m")
    assert code is None and "resource monitoring" in out and "Resources CPU and memory" in out, out


def github_annotations_point_at_the_failing_line():
    from test_junkie.console import github_annotations
    aggregator, _ = _run([ConsoleMixedSuite])
    lines = github_annotations(aggregator)
    assert len(lines) == 1, lines
    assert lines[0].startswith("::error file=tests/junkie_suites/console_checks.py,line=") or \
        "console_checks.py,line=" in lines[0], lines
    assert "title=ConsoleMixedSuite.fails_differently_first::FAIL: AssertionError" in lines[0], lines


CHECKS = [tracebacks_print_as_lines, retried_test_lists_every_run_and_groups_tracebacks,
          output_is_shown_only_for_tests_that_did_not_pass, no_capture_prints_output_live, quiet_run_prints_nothing,
          summary_table_and_verdict, failed_before_class_is_one_entry, per_test_prints_a_line_per_test,
          keyboard_interrupt_in_a_test_cancels_the_run, cancel_stops_retries, parse_traceback_keeps_the_users_frames,
          live_bars_redraw_in_place, ctrl_c_cancels_a_threaded_run, ctrl_c_interrupts_a_sequential_test,
          second_ctrl_c_stops_immediately, resource_chart_sequential_layout,
          resource_chart_threaded_lanes_and_running_row, resource_chart_too_short_to_sample,
          run_with_monitor_resources_prints_the_chart, tj_run_dash_m_reaches_the_run,
          github_annotations_point_at_the_failing_line]
