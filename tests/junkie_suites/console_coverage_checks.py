"""
Console behaviours no other check reaches: colors and terminals, streams that misbehave, the live block, Ctrl+C
messages, -p lines, and the less common Problems and summary entries. Each check asserts what the console prints.
Shared by the pytest and TJ test paths.
"""
import contextlib
import io
import logging
import os
import re
import sys
import time
import types

from test_junkie import console as console_module
from test_junkie.console import (Capture, Console, Router, RunState, _Stream, _capture_record, _color_enabled,
                                 _exception_summary, _relative, _setting_value, github_annotations, parse_traceback,
                                 resource_chart)
from test_junkie.constants import SuiteCategory, TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.errors import TestListenerError
from test_junkie.listener import Listener
from test_junkie.rerun import Rerun
from test_junkie.runner import Runner

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


@contextlib.contextmanager
def _env(**values):
    """Sets (or with None, removes) environment variables for the block"""
    saved = {name: os.environ.get(name) for name in values}
    try:
        for name, value in values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


_NO_COLOR_ENV = dict(NO_COLOR=None, FORCE_COLOR=None, GITHUB_ACTIONS=None)


def _settings(**overrides):
    values = dict(per_test=False, suite_thread_limit=1, test_thread_limit=1, rerun=None, capture=True,
                  monitor_resources=False, retry=None, kwargs={}, html_report=None, xml_report=None, json_report=None,
                  tests=None, owners=None, components=None, features=None, tags=None, from_config={}, config=None,
                  fail_on_flaky=False, flag_flaky=False)
    values.update(overrides)
    return types.SimpleNamespace(**values)


def _console(settings=None, stream=None, **kwargs):
    """A Console that writes to `stream` (a StringIO by default: no colors, no live block)"""
    stream = io.StringIO() if stream is None else stream
    previous = sys.stdout
    sys.stdout = stream
    try:
        return Console(_settings() if settings is None else settings, **kwargs), stream
    finally:
        sys.stdout = previous


class FakeConsoleSuite(object):
    """Just enough of a SuiteObject for the console's own bookkeeping"""

    def __init__(self, name="FakeConsoleSuite"):
        self.name = name
        self.metrics = types.SimpleNamespace(get_metrics=lambda: {"status": SuiteCategory.SUCCESS})

    def get_class_name(self):
        return self.name

    def get_class_object(self):
        return FakeConsoleSuite

    def get_class_module(self):
        return __name__

    def get_parameters(self):
        return []

    def get_test_objects(self):
        return []

    def get_order(self):
        return None

    def get_runtime(self):
        return 0.5


def _empty_aggregator():
    return types.SimpleNamespace(executed_suites=[], get_basic_report=lambda: {"suites": {}, "tests": {"total": 0}})


def _run(suites, **kwargs):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        aggregator = Runner(suites).run(**kwargs)
    return aggregator, out.getvalue()


# ── colors and terminals ────────────────────────────────────────────────────────────────────────────────────────

class _RealStream(io.StringIO):
    """Looks like a real file: has a file descriptor, isn't a terminal"""

    def fileno(self):
        return 1

    def isatty(self):
        return False


class _BrokenTTY(_RealStream):

    def isatty(self):
        raise OSError("isatty not supported")


def force_color_colors_a_real_stream():
    with _env(NO_COLOR=None, FORCE_COLOR="1", GITHUB_ACTIONS=None):
        assert _color_enabled(_RealStream()) is True
        console, _ = _console(stream=_RealStream())
    assert console.style("Total", "bold") == "\x1b[1mTotal\x1b[0m"
    assert console.badge("PASSED", "pass") == "\x1b[1;30;42m PASSED \x1b[0m"
    assert console.style("plain") == "plain"  # no style names: nothing to add


def stream_that_cannot_answer_isatty_is_not_a_terminal():
    with _env(**_NO_COLOR_ENV):
        assert _color_enabled(_BrokenTTY()) is False
        console, stream = _console(stream=_BrokenTTY(), mode="normal")
    console.emit(["hello"])
    assert stream.getvalue() == "hello\n"  # no live block, no colors
    assert console.badge("PASSED", "pass") == "[PASSED]"


class _OsOnWindows(object):
    """os as seen on Windows: name is "nt", everything else is the real module"""
    name = "nt"

    def __getattr__(self, item):
        return getattr(os, item)


def colors_on_windows_set_up_the_console():
    # on Windows a colored console calls colorama first (when it's installed) so ANSI codes work in old terminals
    init = types.FunctionType(Console.__init__.__code__, dict(vars(console_module), os=_OsOnWindows()), "__init__",
                              Console.__init__.__defaults__)
    console = Console.__new__(Console)
    previous = sys.stdout
    sys.stdout = _RealStream()
    try:
        with _env(NO_COLOR=None, FORCE_COLOR="1", GITHUB_ACTIONS=None):
            init(console, _settings())
    finally:
        sys.stdout = previous
    assert console.badge("FAILED", "err") == "\x1b[1;97;41m FAILED \x1b[0m"


def _system_on(platform, windows_version=None):
    fake_sys = types.SimpleNamespace(platform=platform)
    if windows_version is not None:
        fake_sys.getwindowsversion = windows_version
    return types.FunctionType(console_module._system.__code__, dict(vars(console_module), sys=fake_sys))()


def header_names_the_operating_system():
    def unknown():
        raise OSError("no version")

    assert _system_on("win32", unknown) == "Windows"
    assert _system_on("win32", lambda: types.SimpleNamespace(major=10, build=22631)) == "Windows 11"
    assert _system_on("win32", lambda: types.SimpleNamespace(major=10, build=19045)) == "Windows 10"
    assert _system_on("darwin").startswith("macOS")
    assert _system_on("linux") == "Linux"
    assert _system_on("freebsd14") == "freebsd14"


def header_shows_what_a_saved_config_set():
    settings = _settings(config=types.SimpleNamespace(path="tj.cfg"),
                         from_config={"capture": False, "suites": ["Login", "Checkout"]})
    console, stream = _console(settings)
    console.start([FakeConsoleSuite()])
    out = stream.getvalue()
    assert "config   tj.cfg" in out, out
    assert "capture off" in out and "suites Login, Checkout" in out, out
    assert _setting_value(True) == "on" and _setting_value(3) == "3"


# ── streams that misbehave ──────────────────────────────────────────────────────────────────────────────────────

class _NarrowStream(object):
    """Says it's UTF-8 when the console checks, then turns out to be ASCII, and can't be flushed"""

    def __init__(self):
        self.encoding = "utf-8"
        self.parts = []

    def write(self, text):
        text.encode(self.encoding)
        self.parts.append(text)

    def flush(self):
        raise OSError("pipe closed")

    def isatty(self):
        return False


def text_the_stream_cannot_encode_is_replaced():
    stream = _NarrowStream()
    console, _ = _console(stream=stream)
    stream.encoding = "ascii"
    console.emit(["café → done"])
    assert "".join(stream.parts) == "caf? ? done\n", stream.parts


class _BrokenStream(object):

    def write(self, text):
        raise OSError("stream closed")

    def flush(self):
        raise OSError("stream closed")

    def isatty(self):
        raise OSError("stream closed")


def stream_stand_in_writes_flushes_and_survives():
    console, _ = _console(mode="silent")
    router = Router(console, capture_enabled=False)  # not installed: everything goes straight through
    original = io.StringIO()
    stand_in = _Stream(router, original, "out")
    assert stand_in.write(42) == 2
    stand_in.writelines(["a\n", "b\n"])
    assert original.getvalue() == "42a\nb\n"
    broken = _Stream(router, _BrokenStream(), "err")
    broken.flush()  # the error is swallowed
    assert broken.isatty() is False


def log_record_with_bad_arguments_is_still_captured():
    record = logging.LogRecord("payments", logging.WARNING, __file__, 1, "%d items left", ("many",), None)
    capture = Capture()
    _capture_record(object(), [capture], record)
    assert capture.log == [("WARNING", "payments", "%d items left")], capture.log  # the raw message, not an error


# ── output outside the live block ───────────────────────────────────────────────────────────────────────────────

def notes_and_emits_follow_the_mode():
    console, stream = _console(mode="normal")
    console.note("seed 42")
    assert stream.getvalue() == "[NOTE]  seed 42\n", stream.getvalue()
    console, stream = _console(mode="cli-quiet")
    console.note("seed 42")
    assert "seed 42" in stream.getvalue()
    console, stream = _console(mode="silent")
    console.note("seed 42")
    console.emit(["not shown"])
    assert stream.getvalue() == ""


def passthrough_respects_silent_and_broken_streams():
    console, _ = _console(mode="silent")
    out, err = io.StringIO(), io.StringIO()
    assert console.passthrough(out, "print()", "out") == 7
    assert out.getvalue() == ""  # a quiet run swallows what isn't captured
    assert console.passthrough(err, "warning", "err") == 7
    assert err.getvalue() == "warning"  # stderr still goes through
    console, _ = _console(mode="normal")
    assert console.passthrough(_BrokenStream(), "lost", "out") == 4  # a closed stream doesn't break the run


# ── tracebacks ──────────────────────────────────────────────────────────────────────────────────────────────────

def traceback_helpers_handle_partial_input():
    trace = 'Traceback (most recent call last):\n  File "app.py", line 3, in main\nValueError: boom\n'
    frames, exception = parse_traceback(trace)
    assert frames == [("app.py", "3", "main", None)], frames  # no source line under the frame
    assert exception == ["ValueError: boom"], exception
    assert _exception_summary("", ValueError("boom\nsecond line")) == "ValueError: boom"
    assert _exception_summary(None) == ""
    assert _relative("") == ""  # relpath() can't take it - the path is kept as it is


# ── the live block ──────────────────────────────────────────────────────────────────────────────────────────────

class _TTY(io.StringIO):

    def isatty(self):
        return True


def _wait_for(condition, timeout=3.0):
    deadline = time.time() + timeout
    while not condition() and time.time() < deadline:
        time.sleep(0.02)
    return condition()


def live_block_redraws_cuts_long_lines_and_shows_the_cancel():
    tty = _TTY()
    state = RunState()
    suite = FakeConsoleSuite()
    with _env(TJ_NO_LIVE=None, COLUMNS="60", **_NO_COLOR_ENV):
        console, _ = _console(stream=tty, state=state)
        console.start([suite])
        console.suite_started(suite)
        # the redraw thread notices the change: erase the block (cursor up + clear) and draw it again
        assert _wait_for(lambda: "F\x1b[J" in tty.getvalue()), repr(tty.getvalue())
        assert _wait_for(lambda: "running" in tty.getvalue()), repr(tty.getvalue())
        state.cancelled, state.by_user = True, True
        for index in range(9):
            console.unit_started(("step", index), "FakeConsoleSuite.step[{}]".format(index))
        console.suite_cleanup(suite, True)
        console.emit(["tick"])
        drawn = tty.getvalue()
        code = console.finish(_empty_aggregator(), 0.5)
    assert code == 12, code  # cancelled by the user
    lines = [_ANSI.sub("", line) for line in drawn.split("\x1b[2K")[1:]]
    lines = [line.split("\n")[0] for line in lines]
    assert lines and all(len(line) <= 59 for line in lines), lines  # 60 columns: nothing may wrap
    assert any(line.startswith("Total") and len(line) == 59 for line in lines), lines  # the total line was cut
    assert "console_coverage_checks" not in drawn  # too narrow for the file column
    plain = _ANSI.sub("", drawn)
    assert "cleanup" in plain, plain
    assert "CANCELLING" in plain and "... and 1 more" in plain, plain
    assert "FakeConsoleSuite: running @afterClass ..." in plain, plain
    assert "[CANCELLED]  by Ctrl+C" in tty.getvalue(), tty.getvalue()


def cancel_message_without_running_tests():
    console, stream = _console(mode="normal")
    console.cancelling()
    console.cancelling()  # Ctrl+C again before the run ends: the message isn't repeated
    out = stream.getvalue()
    assert out.count("CANCELLING") == 1, out
    assert "Writing the summary and reports ..." in out, out
    console, stream = _console(mode="cli-quiet")
    console.cancelling()
    assert stream.getvalue() == ""  # tj run -q prints only problems and the verdict


def second_ctrl_c_says_what_was_running():
    console, stream = _console(cli={"sources": ["tests"]})
    console.unit_started(("slow",), "CheckoutSuite.pays")
    console.force_stop()
    out = stream.getvalue()
    assert "[STOPPED]  Second Ctrl+C: stopped immediately." in out, out
    assert "1 test was still running: CheckoutSuite.pays (" in out, out
    assert "Cleanup and reports were skipped." in out and "exit code 130" in out, out
    console, stream = _console()
    console.force_stop()
    out = stream.getvalue()
    assert "still running" not in out and "exit code" not in out, out  # Runner.run(): no exit code to speak of


# ── -p: a line per test ─────────────────────────────────────────────────────────────────────────────────────────

_POLICY_RETRIES = [{"policy": "Flaky", "when": '"503"', "waited": 20, "run": 1}]
_WAITS = [{"with": ["BillingSuite", "LedgerSuite"], "seconds": 1.25}, {"with": ["LedgerSuite"], "seconds": 0.25}]


def per_test_line_explains_retries_and_waits():
    console, stream = _console(_settings(per_test=True))
    suite = FakeConsoleSuite()
    console.start([suite])
    console.suite_started(suite)
    console.unit_done(suite, ("pays",), TestCategory.SUCCESS, label="FakeConsoleSuite.pays", runtime=0.25, runs=2,
                      retries=_POLICY_RETRIES, waits=_WAITS)
    out = stream.getvalue()
    assert 'pays' in out and 'passed on run 2 (Flaky, when "503": waited 20s) waited 1.5s ' \
                              '(conflicts with BillingSuite, LedgerSuite)' in out, out
    before = stream.getvalue()
    console.unit_done(FakeConsoleSuite("Unknown"), ("x",), TestCategory.SUCCESS, label="Unknown.x")
    console.unit_done(suite, ("y",), None, label="FakeConsoleSuite.y")  # no result to show
    console.suite_finished(FakeConsoleSuite("Unknown"))
    assert stream.getvalue() == before
    console.suite_started(FakeConsoleSuite("LateSuite"))  # a suite start() didn't know about still gets a heading
    assert stream.getvalue()[len(before):].startswith("LateSuite"), stream.getvalue()


def retry_summary_lists_every_condition():
    assert Console.retry_summary([{"policy": "Network", "when": "ConnectionError", "waited": 0},
                                  {"policy": "Network", "when": "Timeout", "waited": 0},
                                  {"policy": "Network", "when": "Timeout", "waited": 0}]) == \
        "Network, when ConnectionError then Timeout"
    assert Console.retry_summary([{"policy": None, "when": None, "waited": 0}]) == ""  # plain retry=N


def threaded_per_test_lines_print_with_their_suite():
    console, stream = _console(_settings(per_test=True, suite_thread_limit=2))
    suite = FakeConsoleSuite()
    console.start([suite])
    console.suite_started(suite)
    console.unit_done(suite, ("pays",), TestCategory.SUCCESS, label="FakeConsoleSuite.pays", runtime=0.1)
    assert "PASSED" not in stream.getvalue()  # held back so suites running together don't interleave
    console.suite_finished(suite)
    lines = stream.getvalue().splitlines()
    heading = next(index for index, line in enumerate(lines) if line.startswith("FakeConsoleSuite"))
    assert "PASSED" in lines[heading + 1] and "pays" in lines[heading + 1], lines


# ── Problems, summary and verdict from real runs ────────────────────────────────────────────────────────────────

@Suite()
class AnnotatedConsoleSuite:

    @test(parameters=[7])
    def checks_total(self, parameter):
        assert parameter == 8, "expected 8, got {}".format(parameter)


def github_actions_get_annotations_with_parameters():
    with _env(GITHUB_ACTIONS="true", NO_COLOR=None, FORCE_COLOR=None):
        aggregator, out = _run([AnnotatedConsoleSuite], _cli={"sources": ["tests"]})
    assert "title=AnnotatedConsoleSuite.checks_total[7]::FAIL: AssertionError: expected 8, got 7" in out, out
    assert "exit code 1" in out, out
    assert github_annotations(aggregator)[0].startswith("::error file="), github_annotations(aggregator)


@Suite()
class SteadyConsoleSuite:

    @test()
    def steady(self):
        pass


def flag_flaky_with_nothing_flaky():
    _, out = _run([SteadyConsoleSuite], flag_flaky=True)
    assert "Flaky 0" in out and "No test needed a retry to pass." in out, out


@Suite()
class ChattyConsoleSuite:

    @test()
    def talks_a_lot(self):
        for index in range(1, 46):
            print("LINE-{:02d}".format(index))
        raise AssertionError("too chatty")


def long_output_keeps_the_last_40_lines():
    _, out = _run([ChattyConsoleSuite])
    assert "... 5 earlier lines" in out, out
    assert "LINE-05" not in out and "LINE-06" in out and "LINE-45" in out, out


ALTERNATING = {"runs": 0}


@Suite()
class AlternatingConsoleSuite:

    @test(retry=3)
    def alternates(self):
        ALTERNATING["runs"] += 1
        raise ValueError("odd run" if ALTERNATING["runs"] % 2 else "even run")


def runs_with_the_same_traceback_apart_are_listed():
    ALTERNATING["runs"] = 0
    _, out = _run([AlternatingConsoleSuite])
    assert "Runs #1, #3  same traceback both times" in out, out
    assert "Run #2  traceback" in out, out


_GENERATED_SUITE = """
from test_junkie.decorators import Suite, test


@Suite()
class GeneratedConsoleSuite:

    @test(parameters=[1, "1"])
    def same_text(self, parameter):
        pass
"""


def bad_parameters_in_generated_code_still_get_an_entry():
    # a suite built from a string has no source file to point at: the entry says what happened without one
    namespace = {"__name__": "generated_console_suite"}
    exec(compile(_GENERATED_SUITE, "<generated>", "exec"), namespace)
    _, out = _run([namespace["GeneratedConsoleSuite"]])
    assert "[IGNORED] GeneratedConsoleSuite.same_text" in out, out
    detail = [line for line in out.splitlines() if "bad parameters" in line]
    assert detail and detail[0].strip().startswith(". bad parameters . not run"), detail


class RaisesOnSuccess(Listener):

    def on_success(self, **kwargs):
        raise RuntimeError("listener bug")


@Suite(listener=RaisesOnSuccess)
class ListenedConsoleSuite:

    @test(parameters=["alpha"])
    def checks(self, parameter):
        pass


def listener_entry_names_the_parameter():
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            Runner([ListenedConsoleSuite]).run()
        raise AssertionError("expected TestListenerError")
    except TestListenerError:
        pass
    heads = [line for line in out.getvalue().splitlines() if line.startswith("[LISTENER]")]
    assert heads and "ListenedConsoleSuite.checks" in heads[0] and "[alpha]" in heads[0], out.getvalue()


@Suite()
class FirstToRunConsoleSuite:

    @test()
    def first(self):
        pass


@Suite()
class NeverStartedConsoleSuite:

    @test()
    def second(self):
        pass


def cancelled_before_start_lists_every_suite_as_cancelled():
    runner = Runner([FirstToRunConsoleSuite, NeverStartedConsoleSuite])
    runner.cancel()  # before run(): nothing starts
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        runner.run()
    rows = {line.split()[0]: line.split() for line in out.getvalue().splitlines()
            if line.strip().startswith(("FirstToRunConsoleSuite", "NeverStartedConsoleSuite"))}
    assert set(rows) == {"FirstToRunConsoleSuite", "NeverStartedConsoleSuite"}, out.getvalue()
    assert all("1" in row[1:] for row in rows.values()), rows  # each suite's one test, counted as cancelled
    assert "2 tests" in out.getvalue(), out.getvalue()


def rerun_with_nothing_to_rerun_passes():
    _, out = _run([SteadyConsoleSuite], rerun=Rerun())
    assert "[PASSED]  nothing to run again" in out, out


# ── tj run -m chart ─────────────────────────────────────────────────────────────────────────────────────────────

def _plain_style(text, *names):
    return str(text)


def chart_of_a_long_run_counts_minutes():
    lines = resource_chart(_plain_style, [], 0.0, 150.0, [], [])
    assert lines[-1] == "  The run took 2.5m - too short to sample (one sample every 0.25s).", lines


def chart_shortens_suites_that_barely_ran():
    start = 1000.0
    samples = [(start + i * 0.25, 30, 40) for i in range(41)]  # 10 seconds, 60 columns: a column is 1/6 s
    suites = [("AlphaSuite", start, start + 0.2), ("BetaSuite", start + 5.0, start + 5.1)]
    lines = resource_chart(_plain_style, samples, start, start + 10.0, [], suites, width=60)
    lane = next(line for line in lines if line.startswith("  suites "))
    cells = lane[len("  suites "):]
    assert cells[:2] == "├A" and cells[2:30].strip() == "", lane  # two columns: the bracket and a letter
    assert cells[30] == "B" and cells[31:].strip() == "", lane  # one column: just the letter


CHECKS = [force_color_colors_a_real_stream, stream_that_cannot_answer_isatty_is_not_a_terminal,
          colors_on_windows_set_up_the_console, header_names_the_operating_system,
          header_shows_what_a_saved_config_set, text_the_stream_cannot_encode_is_replaced,
          stream_stand_in_writes_flushes_and_survives, log_record_with_bad_arguments_is_still_captured,
          notes_and_emits_follow_the_mode, passthrough_respects_silent_and_broken_streams,
          traceback_helpers_handle_partial_input, live_block_redraws_cuts_long_lines_and_shows_the_cancel,
          cancel_message_without_running_tests, second_ctrl_c_says_what_was_running,
          per_test_line_explains_retries_and_waits, retry_summary_lists_every_condition,
          threaded_per_test_lines_print_with_their_suite, github_actions_get_annotations_with_parameters,
          flag_flaky_with_nothing_flaky, long_output_keeps_the_last_40_lines,
          runs_with_the_same_traceback_apart_are_listed, bad_parameters_in_generated_code_still_get_an_entry,
          listener_entry_names_the_parameter, cancelled_before_start_lists_every_suite_as_cancelled,
          rerun_with_nothing_to_rerun_passes, chart_of_a_long_run_counts_minutes,
          chart_shortens_suites_that_barely_ran]
