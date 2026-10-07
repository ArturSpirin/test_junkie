"""
Everything a run prints: the header, progress bars, the Ctrl+C messages, problems, the summary and the verdict.
Also captures what tests print and log while they run, so it's only shown for tests that didn't pass.
"""
import inspect
import io
import logging
import os
import re
import sys
import threading
import time

import test_junkie
from test_junkie.constants import TestCategory, SuiteCategory

_PACKAGE_DIR = os.path.dirname(os.path.abspath(test_junkie.__file__))
_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_FRAME = re.compile(r'^\s*File "(?P<file>[^"]+)", line (?P<line>\d+), in (?P<func>.+)$')
_CHAINED = re.compile(r"\n(?:During handling of the above exception, another exception occurred:|"
                      r"The above exception was the direct cause of the following exception:)\n")
_BAR_WIDTH = 24
_RULE_WIDTH = 80
_REDRAW_INTERVAL = 0.2

# status -> style name. Bars and suite names take the worst status, in this order
_STYLE_OF = {TestCategory.SUCCESS: "pass", TestCategory.FAIL: "fail", TestCategory.ERROR: "err",
             TestCategory.SKIP: "skip", TestCategory.IGNORE: "ign", TestCategory.CANCEL: "canc"}
_SEVERITY = [TestCategory.ERROR, TestCategory.FAIL, TestCategory.IGNORE]
_COLUMNS = [(TestCategory.SUCCESS, "Pass", 6), (TestCategory.FAIL, "Fail", 6), (TestCategory.ERROR, "Error", 7),
            (TestCategory.IGNORE, "Ignore", 8), (TestCategory.SKIP, "Skip", 6), (TestCategory.CANCEL, "Cancel", 8)]

_CODES = {"pass": "32", "fail": "33", "err": "31", "skip": "34", "ign": "38;5;208", "canc": "90", "warn": "33",
          "dim": "2", "bold": "1", "param": "36"}
_BADGES = {"pass": "30;42", "fail": "30;43", "err": "97;41", "ign": "30;48;5;208", "canc": "97;100", "skip": "97;44"}


def _color_enabled(stream):
    if os.environ.get("NO_COLOR"):
        return False
    try:
        stream.fileno()
    except Exception:  # an in-memory stream (redirect_stdout, pytest's capture): never colored, even in CI
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("GITHUB_ACTIONS"):
        return True
    try:
        return stream.isatty()
    except Exception:
        return False


# for streams that can't encode the box drawing characters (a pipe on Windows is cp1252)
_ASCII = {ord("─"): "-", ord("│"): "|", ord("·"): ".", ord("…"): "...", ord("›"): ">", ord("–"): "-", ord("→"): "->",
          ord("■"): "#"}


def _unicode_ok(stream):
    try:
        "─│·…›–→".encode(getattr(stream, "encoding", None) or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def _system():
    """
    OS name for the header. platform.system()/release() can take 50 ms on Windows (they may query WMI)
    """
    if sys.platform == "win32":
        try:
            version = sys.getwindowsversion()
            return "Windows {}".format(11 if version.major == 10 and version.build >= 22000 else version.major)
        except Exception:
            return "Windows"
    if sys.platform == "darwin":
        import platform
        return "macOS {}".format(platform.mac_ver()[0]).strip()
    if sys.platform.startswith("linux"):
        return "Linux"
    return sys.platform


def _columns():
    import shutil  # only needed for live output
    return shutil.get_terminal_size((100, 24)).columns


def _setting_value(value):
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    return str(value)


def _visible(text):
    return len(_ANSI.sub("", text))


class RunState(object):
    """
    Cancel state shared by the runner, its threads and the Ctrl+C handler for one run()
    """

    def __init__(self, cancelled=False):
        self.cancelled = cancelled
        self.by_user = False  # Ctrl+C or a KeyboardInterrupt, as opposed to Runner.cancel()
        self.interrupts = 0
        self.main_thread_in_test = False

    def __call__(self):
        return self.cancelled


class TestInterrupted(BaseException):
    """
    Raised into a test running on the main thread when Ctrl+C is pressed. BaseException, so `except Exception` in the
    test doesn't swallow it
    """


# ── output capture ─────────────────────────────────────────────────────────────────────────────────────────────────

_LOCAL = threading.local()


class Capture(object):
    """
    What one test run (or one suite's setup/teardown) printed and logged
    """

    def __init__(self):
        self.out = io.StringIO()
        self.log = []

    def output(self):
        return self.out.getvalue()


def _stack(owner):
    stacks = getattr(_LOCAL, "stacks", None)
    if stacks is None:
        stacks = _LOCAL.stacks = {}
    return stacks.setdefault(id(owner), [])


class capturing(object):
    """
    Routes what the current thread prints and logs into `capture` while the block runs. Keyed by the router, so a run
    started inside a test (Test Junkie's own tests do that) captures into its own buffers and the outer run into its
    """

    def __init__(self, router, capture):
        self.__router = router
        self.__capture = capture

    def __enter__(self):
        if self.__router is not None:
            _stack(self.__router).append(self.__capture)
        return self.__capture

    def __exit__(self, *exc):
        if self.__router is not None:
            stack = _stack(self.__router)
            if stack and stack[-1] is self.__capture:
                stack.pop()
        return False


class _Stream(object):
    """
    Stands in for sys.stdout / sys.stderr during a run
    """

    def __init__(self, router, original, kind):
        self.__router = router
        self.__original = original
        self.__kind = kind

    def write(self, text):
        if not isinstance(text, str):
            text = str(text)
        if self.__router.active:
            stack = _stack(self.__router)
            if stack and self.__router.capture_enabled:
                stack[-1].out.write(text)
                return len(text)
            return self.__router.console.passthrough(self.__original, text, self.__kind)
        return self.__original.write(text)

    def writelines(self, lines):
        for line in lines:
            self.write(line)

    def flush(self):
        try:
            self.__original.flush()
        except Exception:
            pass

    def isatty(self):
        try:
            return self.__original.isatty()
        except Exception:
            return False

    @property
    def original(self):
        return self.__original

    def __getattr__(self, name):  # encoding, fileno, buffer, ... - whatever the real stream has
        return getattr(self.__original, name)


class _LogCapture(logging.Handler):

    def __init__(self, router):
        logging.Handler.__init__(self, level=logging.NOTSET)
        self.__router = router

    def emit(self, record):
        if record.name == "TestJunkieLogger":  # -v debug logs stay live
            return
        stack = _stack(self.__router)
        if stack:
            try:
                message = record.getMessage()
            except Exception:
                message = str(record.msg)
            stack[-1].log.append((record.levelname, record.name, message))


class _SkipCaptured(logging.Filter):
    """
    Keeps console log handlers quiet for records a test logged while captured - they're in its captured log instead
    """

    def __init__(self, router):
        logging.Filter.__init__(self)
        self.__router = router

    def filter(self, record):
        return record.name == "TestJunkieLogger" or not _stack(self.__router)


class Router(object):
    """
    Installed for the length of a run(): what a test prints or logs goes into that test's Capture, everything else
    goes to the console (above the live progress bars, so it doesn't break them)
    """

    def __init__(self, console, capture_enabled):
        self.console = console
        self.capture_enabled = capture_enabled
        self.active = False
        self.__stdout = None
        self.__stderr = None
        self.__log_handler = None
        self.__filtered = []

    def install(self):
        self.__stdout = _Stream(self, sys.stdout, "out")
        self.__stderr = _Stream(self, sys.stderr, "err")
        sys.stdout, sys.stderr = self.__stdout, self.__stderr
        self.active = True
        if self.capture_enabled:
            self.__log_handler = _LogCapture(self)
            logging.getLogger().addHandler(self.__log_handler)
            skip = _SkipCaptured(self)
            handlers = [logging.lastResort] if logging.lastResort is not None else []
            loggers = [logging.getLogger()] + [logger for logger in logging.Logger.manager.loggerDict.values()
                                               if isinstance(logger, logging.Logger)]
            for logger in loggers:
                handlers.extend(logger.handlers)
            for handler in handlers:
                if isinstance(handler, logging.StreamHandler) and handler is not self.__log_handler:
                    handler.addFilter(skip)
                    self.__filtered.append((handler, skip))

    def uninstall(self):
        self.active = False
        # only put the real streams back if nothing replaced ours since - otherwise ours stays in the chain, but
        # inactive it just passes everything through
        if sys.stdout is self.__stdout:
            sys.stdout = self.__stdout.original
        if sys.stderr is self.__stderr:
            sys.stderr = self.__stderr.original
        if self.__log_handler is not None:
            logging.getLogger().removeHandler(self.__log_handler)
        for handler, skip in self.__filtered:
            handler.removeFilter(skip)
        self.__filtered = []


# ── tracebacks ─────────────────────────────────────────────────────────────────────────────────────────────────────

def _relative(path):
    try:
        relative = os.path.relpath(path)
        return path if relative.startswith(".." + os.sep + "..") else relative
    except ValueError:  # another drive on Windows
        return path


def parse_traceback(text):
    """
    :return: (frames, exception lines). Frames are (file, line, function, source line or None) outside of Test
             Junkie's own code. Only the last exception of a chain is kept
    """
    if not text:
        return [], []
    text = _CHAINED.split(text)[-1]
    lines = text.rstrip("\n").split("\n")
    frames, last = [], -1
    for index, line in enumerate(lines):
        match = _FRAME.match(line)
        if not match:
            continue
        source = None
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if following.startswith("    ") and not _FRAME.match(following):
            source = following.strip()
            last = index + 1
        else:
            last = index
        path = match.group("file")
        if not os.path.abspath(path).startswith(_PACKAGE_DIR + os.sep):
            frames.append((_relative(path), match.group("line"), match.group("func"), source))
    rest = lines[last + 1:] if last >= 0 else lines
    exception = [line for line in rest
                 if line.strip() and set(line.strip()) - set("^~ ") and line.strip() != "Traceback (most recent call last):"]
    exception = [line[len("test_junkie.errors."):] if line.startswith("test_junkie.errors.") else line
                 for line in exception]
    return frames, exception


def _exception_summary(trace, exception=None):
    frames, lines = parse_traceback(trace)
    if lines:
        return lines[0].strip()
    if exception is not None:
        return "{}: {}".format(type(exception).__name__, exception).split("\n")[0]
    return ""


# ── the console ────────────────────────────────────────────────────────────────────────────────────────────────────

class _SuiteProgress(object):

    def __init__(self, suite, expected):
        self.suite = suite
        self.expected = expected
        self.done = {}  # unit key -> status
        self.started = None
        self.finished = None
        self.cleanup = False
        self.lines = []  # -p in a threaded run: printed together when the suite finishes

    def total(self):
        return max(self.expected, len(self.done))

    def ran(self):
        return sum(1 for status in self.done.values() if status != TestCategory.CANCEL)

    def suite_status(self):
        """
        :return: the suite's status when it was skipped, ignored or cancelled as a whole (no test ran), else None
        """
        status = self.suite.metrics.get_metrics().get("status")
        if self.finished and not self.done and status in (SuiteCategory.SKIP, SuiteCategory.IGNORE,
                                                          SuiteCategory.CANCEL):
            return status
        return None

    def processed(self):
        """
        Results that are final and not cancelled - what the bars count as done
        """
        return self.expected if self.suite_status() in (SuiteCategory.SKIP, SuiteCategory.IGNORE) else self.ran()

    def cancelled(self):
        return sum(1 for status in self.done.values() if status == TestCategory.CANCEL)

    def worst(self):
        statuses = set(self.done.values())
        for status in _SEVERITY:
            if status in statuses:
                return status
        return TestCategory.SUCCESS


def expected_units(suite):
    """
    How many results a suite will produce, from what's known before it runs. Parameters given as functions count as 1
    until the runner evaluates them
    """
    class_params = suite.get_parameters()
    suite_count = len(class_params) if isinstance(class_params, list) and class_params else 1
    total = 0
    for test in suite.get_test_objects():
        params = test.get_parameters()
        count = len(params) if isinstance(params, list) and params else 1
        total += count * (suite_count if test.accepts_suite_parameters() else 1)
    return total


def unit_key(test, param, class_param):
    return test.get_test_id(), str(class_param if test.accepts_suite_parameters() else None), str(param)


def _short(value, limit=60):
    text = str(value)
    return text if len(text) <= limit else text[:limit - 1] + "…"


class Console(object):
    """
    :param mode: "normal", "cli-quiet" (tj run -q: problems and the verdict only), "silent" (Runner.run(quiet=True))
                 or "report" (problems and summary of results that already exist)
    """

    def __init__(self, settings, mode="normal", cli=None, state=None):
        self.__settings = settings
        self.__mode = mode
        self.__cli = cli or {}
        self.__state = state or RunState()
        self.__stream = sys.stdout
        self.__unicode = _unicode_ok(self.__stream)
        self.__color = _color_enabled(self.__stream)
        if self.__color and os.name == "nt":
            try:
                import colorama
                colorama.just_fix_windows_console()
            except Exception:
                pass
        try:
            tty = self.__stream.isatty()
        except Exception:
            tty = False
        self.__live = tty and mode == "normal" and not os.environ.get("TJ_NO_LIVE")
        self.__per_test = bool(settings.per_test) if settings is not None else False
        self.__threaded = settings is not None and (settings.suite_thread_limit or 1) > 1
        self.__lock = threading.RLock()
        self.__suites = []  # _SuiteProgress, in the order suites started
        self.__progress = {}  # suite -> _SuiteProgress
        self.__running = {}  # unit key -> (label, start time)
        self.__drawn = 0
        self.__partial = False
        self.__dirty = False
        self.__stop = threading.Event()
        self.__thread = None
        self.__name_width = 10
        self.__path_width = 0
        self.__cancel_shown = False
        self.__start = time.time()
        self.__all = []
        self.__count_width = 5
        self.__waiting_for = set()

    # ── styling ──

    def style(self, text, *names):
        if not self.__color or not names:
            return str(text)
        return "\x1b[{}m{}\x1b[0m".format(";".join(_CODES[name] for name in names), text)

    def badge(self, text, name):
        if not self.__color:
            return "[{}]".format(text)
        return "\x1b[1;{}m {} \x1b[0m".format(_BADGES[name], text)

    def rule(self, title, extra=""):
        used = len(title) + 1 + (len(extra) + 1 if extra else 0)
        return "{} {}".format(self.style(title, "bold"),
                              self.style("{}{}".format(extra + " " if extra else "", "─" * (_RULE_WIDTH - used)), "dim"))

    # ── writing ──

    def __write(self, text):
        if not self.__unicode:
            text = text.translate(_ASCII)
        try:
            self.__stream.write(text)
        except UnicodeEncodeError:
            encoding = getattr(self.__stream, "encoding", None) or "ascii"
            self.__stream.write(text.encode(encoding, errors="replace").decode(encoding))
        try:
            self.__stream.flush()
        except Exception:
            pass

    def __erase(self):
        if self.__drawn:
            self.__write("\x1b[{}F\x1b[J".format(self.__drawn))
            self.__drawn = 0

    def __draw(self):
        if not self.__live or self.__partial:
            return
        lines = self.__live_lines()
        width = max(20, _columns() - 1)
        out = []
        for line in lines:
            if _visible(line) > width:  # a wrapped line would break the cursor math, cut it
                line = _ANSI.sub("", line)[:width]
            out.append(line)
        self.__write("".join("\x1b[2K{}\n".format(line) for line in out))
        self.__drawn = len(out)
        self.__dirty = False

    def emit(self, lines):
        """
        Prints lines that stay, above the live block
        """
        if self.__mode == "silent":
            return
        with self.__lock:
            self.__erase()
            self.__write("".join(line + "\n" for line in lines))
            self.__draw()

    def passthrough(self, original, text, kind):
        """
        Output that wasn't captured (no test was running on that thread, or capture is off)
        """
        if self.__mode == "silent" and kind == "out":
            return len(text)
        with self.__lock:
            self.__erase()
            try:
                original.write(text)
                original.flush()
            except Exception:
                pass
            self.__partial = not text.endswith("\n")
            self.__draw()
        return len(text)

    def __loop(self):
        while not self.__stop.wait(_REDRAW_INTERVAL):
            with self.__lock:
                if self.__dirty or self.__state.cancelled:
                    self.__erase()
                    self.__draw()

    # ── layout ──

    def __layout(self, suites):
        names = [suite.get_class_name() for suite in suites] + ["Total"]
        self.__name_width = min(max(len(name) for name in names), 30)
        paths = [self.__path(suite) for suite in suites]
        self.__path_width = min(max([len(path) for path in paths] or [0]), 36)
        columns = _columns()
        if self.__name_width + self.__path_width + _BAR_WIDTH + 30 > columns:
            self.__path_width = 0

    @staticmethod
    def __path(suite):
        try:
            return _relative(inspect.getsourcefile(suite.get_class_object()) or "")
        except Exception:
            return ""

    def __bar(self, done, total, worst, cancelled=0):
        total = max(total, 1)
        filled = min(_BAR_WIDTH, int(round(_BAR_WIDTH * done / float(total))))
        gray = min(_BAR_WIDTH - filled, int(round(_BAR_WIDTH * (done + cancelled) / float(total))) - filled)
        return "[{}{}{}]".format(self.style("|" * filled, _STYLE_OF[worst]) if filled else "",
                                 self.style("|" * gray, "canc") if gray > 0 else "",
                                 self.style("·" * (_BAR_WIDTH - filled - max(gray, 0)), "dim"))

    def __suite_line(self, progress, tail):
        suite = progress.suite
        name = suite.get_class_name()[:self.__name_width].ljust(self.__name_width)
        line = self.style(name, "bold") + "  "
        if self.__path_width:
            line += self.style(self.__path(suite)[:self.__path_width].ljust(self.__path_width), "dim") + "  "
        total = progress.total()
        done, cancelled = progress.processed(), progress.cancelled()
        whole = progress.suite_status()
        if whole == SuiteCategory.CANCEL or (progress.finished and self.__state.cancelled):
            cancelled = total - done  # never started
        worst = {SuiteCategory.SKIP: TestCategory.SKIP, SuiteCategory.IGNORE: TestCategory.IGNORE}.get(
            whole, progress.worst())
        count = "{}/{}".format(done, total).rjust(self.__count_width)
        return "{}{}  {}  {}".format(line, self.__bar(done, total, worst, cancelled), count, tail)

    def __total_line(self, elapsed, final=False):
        done = sum(p.processed() for p in self.__suites)
        total = sum(p.total() for p in self.__suites) + sum(p.expected for p in self.__pending())
        total = max(total, done, 1)
        worst = TestCategory.SUCCESS
        statuses = set(status for p in self.__suites for status in p.done.values())
        statuses.update(TestCategory.IGNORE for p in self.__suites if p.suite_status() == SuiteCategory.IGNORE)
        for status in _SEVERITY:
            if status in statuses:
                worst = status
                break
        cancelled = sum(p.cancelled() for p in self.__suites)
        if final and self.__state.cancelled:
            cancelled = total - done
        width = self.__name_width + 2 + (self.__path_width + 2 if self.__path_width else 0)
        percent = "{}%".format(int(round(100.0 * done / total))).rjust(4)
        return "{}{}  {}  {}  {}".format(self.style("Total".ljust(width), "bold"), self.__bar(done, total, worst, cancelled),
                                         "{}/{}".format(done, total).rjust(self.__count_width), percent,
                                         self.style("{:0.1f}s".format(elapsed), "dim"))

    def __pending(self):
        return [p for p in self.__all if p.started is None]

    def __live_lines(self):
        lines = []
        if not self.__per_test:
            for progress in self.__suites:
                if progress.started is not None and progress.finished is None:
                    tail = "cleanup" if progress.cleanup else ("cancelling" if self.__state.cancelled else "running")
                    lines.append(self.__suite_line(progress, self.style(tail, "dim")))
            lines.append("")
        lines.append(self.__total_line(time.time() - self.__start))
        if self.__state.cancelled and self.__state.by_user:
            lines.append("")
            lines.extend(self.__cancel_block())
        return lines

    def __cancel_block(self, final_stop=False):
        now = time.time()
        running = sorted(self.__running.values(), key=lambda item: item[1])
        lines = ["{}  Ctrl+C received. No new tests will start and nothing is retried.".format(
            self.badge("CANCELLING", "canc"))]
        indent = " " * 15
        if running:
            lines.append("{}Waiting for {} test{} in progress to finish, then cleanup (@afterTest, @afterClass, rules)."
                         .format(indent, self.style(len(running), "bold"), "" if len(running) == 1 else "s"))
            for label, started in running[:8]:
                lines.append("{}  {} {}  {}".format(indent, self.style("›", "dim"), label,
                                                    self.style("running {:0.1f}s".format(now - started), "dim")))
            if len(running) > 8:
                lines.append("{}  {}".format(indent, self.style("… and {} more".format(len(running) - 8), "dim")))
        cleanup = [p.suite.get_class_name() for p in self.__suites if p.cleanup and p.finished is None]
        if cleanup:
            lines.append("{}{}".format(indent, self.style("{}: running @afterClass …".format(", ".join(cleanup)), "dim")))
        if not running and not cleanup:
            lines.append("{}Writing the summary and reports …".format(indent))
        lines.append("{}{} {}".format(indent, self.style("Press Ctrl+C again to stop immediately.", "warn"),
                                      self.style("Cleanup and reports will be skipped.", "dim")))
        return lines

    # ── events from the runner ──

    def start(self, suites):
        self.__all = [_SuiteProgress(suite, expected_units(suite)) for suite in suites]
        self.__progress = {p.suite: p for p in self.__all}
        self.__count_width = len(str(max(sum(p.expected for p in self.__all), 1))) * 2 + 1
        self.__layout(suites)
        if self.__mode != "normal":
            return
        self.emit(self.__header())
        if self.__live:
            self.__thread = threading.Thread(target=self.__loop, name="TestJunkieConsole", daemon=True)
            self.__thread.start()

    def head(self, rows):
        """
        :param rows: LIST of (label, value) printed under the version line, e.g. ("tests", "5 suites, 13 tests")
        :return: LIST of lines - the header tj run and tj audit start with
        """
        dot = self.style(" · ", "dim")
        lines = ["{} {}{}Python {}{}{}".format(self.style("Test Junkie", "bold"), test_junkie.__version__, dot,
                                              "{}.{}.{}".format(*sys.version_info[:3]), dot, _system())]
        lines.extend("  {} {}".format(self.style(label.ljust(8), "dim"), value) for label, value in rows)
        lines.append("")
        return lines

    def found(self, sources, suites, tests, seconds=None):
        """
        :return: STRING, the header's "tests" value: where, how many suites and tests, how long the scan took
        """
        dot = self.style(" · ", "dim")
        value = ("{}{}".format(", ".join(sources), dot) if sources else "") + "{} suite{}, {} test{}".format(
            self.style(suites, "bold"), "" if suites == 1 else "s", self.style(tests, "bold"), "" if tests == 1 else "s")
        if seconds is not None:
            value += dot + self.style("found in {:0.2f}s".format(seconds), "dim")
        return value

    def __header(self):
        settings = self.__settings
        dot = self.style(" · ", "dim")
        rows = []

        def row(label, value):
            rows.append((label, value))

        row("tests", self.found(self.__cli.get("sources"), len(self.__all), sum(p.expected for p in self.__all),
                                self.__cli.get("scan_seconds")))
        suite_threads, test_threads = settings.suite_thread_limit or 1, settings.test_thread_limit or 1
        if suite_threads > 1 or test_threads > 1:
            mode = "parallel{}{} suite thread{}{}{} test thread{}".format(
                dot, suite_threads, "" if suite_threads == 1 else "s", dot, test_threads, "" if test_threads == 1 else "s")
        else:
            mode = "sequential"
        if self.__per_test:
            mode += dot + "one line per test"
        if not settings.capture:
            mode += dot + "test output shown live"
        row("mode", mode)
        reports = []
        if settings.html_report:
            reports.append("html {}".format(settings.html_report))
        if settings.xml_report:
            reports.append("xml {}".format(settings.xml_report))
        if reports:
            row("reports", dot.join(reports))
        filters = []
        for label, value in (("tests", settings.tests), ("owners", settings.owners), ("components", settings.components),
                             ("features", settings.features)):
            if value:
                filters.append("{} {}".format(label, ", ".join(str(getattr(item, "__name__", item)) for item in value)))
        tags = settings.tags or {}
        for key in ("run_on_match_all", "run_on_match_any", "skip_on_match_all", "skip_on_match_any"):
            if tags.get(key):
                filters.append("{} {}".format(key, ", ".join(str(tag) for tag in tags[key])))
        if filters:
            row("filters", dot.join(filters))
        saved = dict(self.__cli.get("from_config") or {})
        saved.update(settings.from_config)
        if saved and settings.config is not None:
            # a saved config changed this run - say so, where it is, and what it set
            row("config", self.style(settings.config.path, "dim"))
            row("", dot.join("{} {}".format(name, self.style(_setting_value(value), "bold"))
                             for name, value in sorted(saved.items())))
        return self.head(rows)

    def suite_started(self, suite):
        with self.__lock:
            progress = self.__progress.get(suite)
            if progress is None:
                progress = self.__progress[suite] = _SuiteProgress(suite, expected_units(suite))
                self.__all.append(progress)
            if progress.started is None:
                progress.started = time.time()
                self.__suites.append(progress)
            self.__dirty = True
        if self.__per_test and not self.__threaded and self.__mode == "normal":
            self.emit([self.__suite_heading(suite)])

    def __suite_heading(self, suite):
        path = self.__path(suite)
        return "{}{}".format(self.style(suite.get_class_name(), "bold"),
                             "  " + self.style(path, "dim") if path else "")

    def unit_started(self, key, label):
        with self.__lock:
            self.__running[key] = (label, time.time())

    def unit_done(self, suite, key, status, label=None, runtime=None, runs=None):
        with self.__lock:
            self.__running.pop(key, None)
            progress = self.__progress.get(suite)
            if progress is None or status is None:
                return
            if progress.started is None:
                progress.started = time.time()
                self.__suites.append(progress)
            progress.done[key] = status
            self.__dirty = True
            line = None
            if self.__per_test and label is not None:
                prefix = suite.get_class_name() + "."
                line = self.__test_line(status, label[len(prefix):] if label.startswith(prefix) else label, runtime,
                                        runs)
                if self.__threaded:
                    progress.lines.append(line)
                    line = None
            if key in self.__waiting_for and not self.__live and self.__mode == "normal":
                # no live block to count down: one line per test that was running when Ctrl+C came
                self.__waiting_for.discard(key)
                self.emit(["  finished {} ({})".format(label or key[0], status)])
        if line is not None and self.__mode == "normal":
            self.emit([line])

    def __test_line(self, status, label, runtime, runs):
        words = {TestCategory.SUCCESS: "PASSED", TestCategory.FAIL: "FAILED", TestCategory.ERROR: "ERROR",
                 TestCategory.SKIP: "SKIPPED", TestCategory.IGNORE: "IGNORED", TestCategory.CANCEL: "CANCELLED"}
        word = words.get(status, str(status).upper())
        if status == TestCategory.SUCCESS and runs and runs > 1:
            word = "RETRIED"
        note = "run {}/{}".format(runs, runs) if runs and runs > 1 and status != TestCategory.SUCCESS else (
            "passed on run {}".format(runs) if runs and runs > 1 else "")
        done = sum(len(p.done) for p in self.__suites)
        total = max(sum(p.total() for p in self.__all), done, 1)
        return "  {}  {}  {}  {}  {}".format(
            self.style(word.ljust(9), _STYLE_OF.get(status, "dim")), label.ljust(44), self.style(note.ljust(18), "dim"),
            "{:0.2f}s".format(runtime).rjust(6) if runtime is not None else "      ",
            self.style("[{}%]".format(str(int(100.0 * done / total)).rjust(3)), "dim"))

    def suite_cleanup(self, suite, active):
        with self.__lock:
            progress = self.__progress.get(suite)
            if progress is not None:
                progress.cleanup = active
                self.__dirty = True

    def suite_finished(self, suite):
        with self.__lock:
            progress = self.__progress.get(suite)
            if progress is None:
                return
            if progress.started is None:
                progress.started = time.time()
                self.__suites.append(progress)
            progress.finished = time.time()
            progress.cleanup = False
            status = suite.metrics.get_metrics()["status"]
            if not progress.done and status in (SuiteCategory.CANCEL, SuiteCategory.IGNORE, SuiteCategory.SKIP):
                tail = {SuiteCategory.CANCEL: ("cancelled", "canc"), SuiteCategory.IGNORE: ("ignored", "ign"),
                        SuiteCategory.SKIP: ("skipped", "skip")}[status]
                line = self.__suite_line(progress, self.style(tail[0], tail[1]))
            else:
                not_run = progress.total() - progress.processed()
                if self.__state.cancelled and not_run > 0:
                    tail = self.style("{} cancelled".format(not_run), "canc")
                else:
                    tail = self.style("{:0.2f}s".format(suite.get_runtime() or 0), "dim")
                line = self.__suite_line(progress, tail)
            lines = progress.lines
            self.__dirty = True
        if self.__mode != "normal":
            return
        if self.__per_test:
            if lines:
                self.emit([self.__suite_heading(suite)] + lines + [""])
            elif not self.__threaded:
                self.emit([""])
        else:
            self.emit([line])

    def cancelling(self):
        with self.__lock:
            self.__dirty = True
            self.__waiting_for = set(self.__running)
            if self.__live or self.__mode != "normal" or self.__cancel_shown:
                return
            self.__cancel_shown = True
            lines = [""] + self.__cancel_block()
        self.emit(lines)

    def force_stop(self):
        """
        Second Ctrl+C: tell the user what was still running, the caller exits right after
        """
        with self.__lock:
            self.__erase()
            now = time.time()
            running = sorted(self.__running.values(), key=lambda item: item[1])
            lines = ["{}  Second Ctrl+C: stopped immediately.".format(self.badge("STOPPED", "err"))]
            indent = " " * 12
            if running:
                lines.append(indent + self.style("{} test{} still running: {}.".format(
                    len(running), " was" if len(running) == 1 else "s were",
                    ", ".join("{} ({:0.1f}s)".format(label, now - started) for label, started in running[:5])), "dim"))
            lines.append(indent + self.style("Cleanup and reports were skipped. Browsers or other resources it opened "
                                             "may still be open.", "dim"))
            if self.__cli:
                lines.append(indent + self.style("exit code 130", "dim"))
            self.__live = False
            self.__write("\n".join(lines) + "\n")

    def finish(self, aggregator, runtime, errors=None):
        """
        Stops the live block and prints problems, the summary and the verdict
        :return: INT, the exit code the CLI uses
        """
        self.__stop.set()
        if self.__thread is not None:
            self.__thread.join(1)
        counts, rows = self.__counts(aggregator)
        code = self.exit_code(counts, aggregator, errors)
        with self.__lock:
            self.__erase()
            self.__live = False
            self.__partial = False
        if self.__mode == "silent":
            return code
        problems = self.problems(aggregator)
        lines = []
        if self.__mode == "normal":
            lines.extend(([] if self.__per_test else [""]) + [self.__total_line(runtime, final=True), ""])
        if problems:
            lines.append(self.rule("Problems", str(len(problems))))
            lines.append("")
            for entry in problems:
                lines.extend(entry)
                lines.append("")
        if self.__mode in ("normal", "report"):
            lines.extend(self.__summary(rows, counts, runtime))
        lines.append(self.__verdict(code, counts, runtime, errors))
        self.emit(lines)
        return code

    def exit_code(self, counts, aggregator, errors):
        if errors:
            return 120
        if self.__state.cancelled and self.__state.by_user:
            return 12
        bad = counts[TestCategory.FAIL] + counts[TestCategory.ERROR] + counts[TestCategory.IGNORE]
        if bad or aggregator.get_basic_report()["tests"]["total"] == 0:
            return 1
        return 0

    # ── problems ──

    def __params(self, test, param, class_param):
        parts = []
        if class_param is not None and test.accepts_suite_parameters():
            parts.append("suite: {}".format(_short(class_param, 40)))
        if param is not None:
            parts.append(_short(param))
        return self.style("[{}]".format(", ".join(parts)), "param") if parts else ""

    def __trace_lines(self, trace, status, exception=None):
        frames, exception_lines = parse_traceback(trace)
        bar = self.style("│", "dim")
        lines = []
        for path, line, func, source in frames:
            lines.append("  {} {}:{} in {}".format(bar, path, line, func))
            if source:
                lines.append("  {}     {}".format(bar, source))
        if not exception_lines and exception is not None:
            exception_lines = "{}: {}".format(type(exception).__name__, exception).split("\n")
        for text in exception_lines[:12]:
            lines.append("  {} {}".format(bar, self.style(text.strip() if not text.startswith(" ") else text,
                                                          _STYLE_OF[status])))
        return lines

    def __captured(self, output, log, label):
        lines = []
        bar = self.style("│", "dim")
        if output and output.strip():
            lines.append("")
            lines.append("  {}  {}".format(self.style("Output", "bold"), self.style(label, "dim")))
            text = output.rstrip("\n").split("\n")
            if len(text) > 40:
                lines.append("  {} {}".format(bar, self.style("… {} earlier lines".format(len(text) - 40), "dim")))
                text = text[-40:]
            lines.extend("  {} {}".format(bar, line) for line in text)
        if log:
            lines.append("")
            lines.append("  {}  {}".format(self.style("Log", "bold"), self.style(label, "dim")))
            for level, name, message in log[-40:]:
                style = "err" if level in ("ERROR", "CRITICAL") else ("warn" if level == "WARNING" else "dim")
                lines.append("  {} {}  {}  {}".format(bar, self.style(level.ljust(8), style), name, message))
        return lines

    @staticmethod
    def __runs_label(indexes):
        numbers = [index + 1 for index in indexes]
        if len(numbers) == 1:
            return "Run #{}".format(numbers[0])
        if numbers == list(range(numbers[0], numbers[-1] + 1)):
            return "Runs #{}–#{}".format(numbers[0], numbers[-1])
        return "Runs " + ", ".join("#{}".format(n) for n in numbers)

    def __location(self, trace, test=None):
        frames, _ = parse_traceback(trace)
        if frames:
            name = test.get_function_name() if test is not None else None
            own = [frame for frame in frames if frame[2] == name]  # the test's own line, not a helper it called
            frame = own[-1] if own else frames[-1]
            return "{}:{}".format(frame[0], frame[1])
        if test is not None:
            try:
                function = test.get_function_object()
                return "{}:{}".format(_relative(inspect.getsourcefile(function)), function.__code__.co_firstlineno)
            except Exception:
                pass
        return ""

    def problems(self, aggregator):
        """
        :return: LIST of entries, each a LIST of lines - one per result that wasn't a pass, skip or cancel
        """
        entries = []
        dot = self.style(" · ", "dim")
        for suite in aggregator.executed_suites:
            suite_metrics = suite.metrics.get_metrics()
            if suite_metrics.get("status") == SuiteCategory.IGNORE:
                reason = suite_metrics.get("initiation_error")
                entry = ["{} {}  {}".format(self.badge("IGNORED", "ign"), self.style(suite.get_class_name(), "bold"),
                                            self.style("whole suite", "dim")),
                         "          " + self.style("{}{}{} tests not run".format(
                             self.__path(suite) or suite.get_class_module(), dot, expected_units(suite)), "dim"),
                         ""]
                if isinstance(reason, str):
                    entry.extend(self.__trace_lines(reason, TestCategory.IGNORE))
                elif reason is not None:
                    entry.append("  {} {}".format(self.style("│", "dim"),
                                                  self.style("{}: {}".format(type(reason).__name__, reason), "ign")))
                entries.append(entry)
                continue
            before_class = [trace for trace in suite_metrics.get("beforeClass", {}).get("tracebacks", []) if trace]
            suite_wide = {}
            for test in suite.get_test_objects():
                for class_param, by_param in test.metrics.get_metrics().items():
                    for param, data in by_param.items():
                        status = data.get("status")
                        if status not in TestCategory.ALL_UN_SUCCESSFUL:
                            continue
                        traces = data.get("tracebacks", [])
                        last = next((t for t in reversed(traces) if t), None)
                        if status == TestCategory.IGNORE and last and (
                                "__run_before_class" in last or any(trace in last for trace in before_class)):
                            suite_wide.setdefault(last, []).append(test)  # @beforeClass failed: one entry
                            continue
                        entries.append(self.__unit_entry(suite, test, data))
            for trace, tests in suite_wide.items():
                entry = ["{} {}  {}".format(self.badge("IGNORED", "ign"), self.style(suite.get_class_name(), "bold"),
                                            self.style("whole suite", "dim")),
                         "          " + self.style("{}{}@beforeClass failed{}{} test{} not run".format(
                             self.__location(trace) or self.__path(suite), dot, dot, len(tests),
                             "" if len(tests) == 1 else "s"), "dim"),
                         "", "  " + self.style("Traceback", "bold")]
                entry.extend(self.__trace_lines(trace, TestCategory.IGNORE))
                for output, log in suite.metrics.get_outputs()[-1:]:
                    entry.extend(self.__captured(output, log, "@beforeClass"))
                entries.append(entry)
        return entries

    def __unit_entry(self, suite, test, data):
        dot = self.style(" · ", "dim")
        status = data["status"]
        param, class_param = data.get("param"), data.get("class_param")
        statuses = data.get("statuses") or [status]
        traces = data.get("tracebacks") or []
        exceptions = data.get("exceptions") or []
        times = data.get("performance") or []
        word, style = {TestCategory.FAIL: ("FAIL", "fail"), TestCategory.ERROR: ("ERROR", "err"),
                       TestCategory.IGNORE: ("IGNORED", "ign")}[status]
        name = "{}.{}".format(suite.get_class_name(), test.get_function_name())
        head = "{} {}".format(self.badge(word, style), self.style(name, "bold"))
        params = self.__params(test, param, class_param)
        if params:
            head += "  " + params
        last_trace = next((t for t in reversed(traces) if t), None)
        indent = " " * (len(word) + 3)
        if status == TestCategory.IGNORE:
            detail = "{}{}not run".format(self.__location(last_trace, test), dot)
            if last_trace and "BadParameters" in last_trace:
                detail = "{}{}bad parameters{}not run".format(self.__location(None, test), dot, dot)
        else:
            runs = len(statuses)
            detail = "{}{}{}{}{:0.2f}s".format(self.__location(last_trace, test), dot,
                                               "failed all {} runs".format(runs) if runs > 1 else "1 run", dot,
                                               sum(t for t in times if t))
        entry = [head, indent + self.style(detail, "dim")]
        if len(statuses) > 1:
            entry.extend(["", "  " + self.style("Runs", "bold")])
            for index, run_status in enumerate(statuses):
                trace = traces[index] if index < len(traces) else None
                exception = exceptions[index] if index < len(exceptions) else None
                summary = _exception_summary(trace, exception)
                runtime = times[index] if index < len(times) else 0
                entry.append("    #{}  {}  {}  {}".format(
                    index + 1, self.style(str(run_status).upper().ljust(6), _STYLE_OF.get(run_status, "dim")),
                    "{:0.2f}s".format(runtime or 0), self.style(summary, _STYLE_OF.get(run_status, "dim"))))
        groups = []  # (trace, [run indexes]) in order of first appearance
        for index, trace in enumerate(traces):
            if not trace:
                continue
            for group in groups:
                if group[0] == trace:
                    group[1].append(index)
                    break
            else:
                groups.append((trace, [index]))
        if status == TestCategory.IGNORE and last_trace and "BadParameters" in last_trace:
            _, lines = parse_traceback(last_trace)
            entry.append("")
            entry.extend("  {} {}".format(self.style("│", "dim"), self.style(line.strip(), "ign")) for line in lines[:4])
        else:
            for trace, indexes in groups:
                entry.append("")
                if len(statuses) > 1:
                    label = self.__runs_label(indexes)
                    note = "traceback" if len(indexes) == 1 else (
                        "same traceback both times" if len(indexes) == 2 else "same traceback each time")
                    entry.append("  {}  {}".format(self.style(label, "bold"), self.style(note, "dim")))
                else:
                    entry.append("  " + self.style("Traceback", "bold"))
                run_status = statuses[indexes[-1]] if indexes[-1] < len(statuses) else status
                exception = exceptions[indexes[-1]] if indexes[-1] < len(exceptions) else None
                entry.extend(self.__trace_lines(trace, run_status if run_status in _STYLE_OF else status, exception))
        outputs = test.metrics.get_outputs(param, class_param)
        if outputs and outputs[-1][0] == len(statuses):  # only the last run's - an earlier run's would mislead
            run, output, log = outputs[-1]
            entry.extend(self.__captured(output, log, "run #{}".format(run) if len(statuses) > 1 else ""))
        return entry

    # ── summary ──

    def __counts(self, aggregator):
        report = aggregator.get_basic_report()["suites"]
        counts = {status: 0 for status, _, _ in _COLUMNS}
        rows = []
        for suite in aggregator.executed_suites:
            row = dict((status, report.get(suite, {}).get(status, 0)) for status, _, _ in _COLUMNS)
            status = suite.metrics.get_metrics().get("status")
            if not any(row.values()) and status in (SuiteCategory.CANCEL, SuiteCategory.IGNORE, SuiteCategory.SKIP):
                # nothing ran, so nothing was recorded per test - count the suite's tests under its status
                row[status] = expected_units(suite)
            elif self.__state.cancelled:
                progress = self.__progress.get(suite)
                if progress is not None:
                    row[TestCategory.CANCEL] += max(0, progress.expected - sum(row.values()))
            for key in counts:
                counts[key] += row[key]
            rows.append((suite, row))
        known = set(aggregator.executed_suites)
        if self.__state.cancelled:
            for progress in self.__all:
                if progress.suite not in known:
                    row = dict((status, 0) for status, _, _ in _COLUMNS)
                    row[TestCategory.CANCEL] = progress.expected
                    counts[TestCategory.CANCEL] += progress.expected
                    rows.append((progress.suite, row))
        return counts, rows

    def __summary(self, rows, counts, runtime):
        names = [suite.get_class_name() for suite, _ in rows]
        labels = []
        for suite, _ in rows:
            name = suite.get_class_name()
            labels.append("{}.{}".format(suite.get_class_module(), name) if names.count(name) > 1 else name)
        width = max([len(label) for label in labels] + [8]) + 2
        header = "  " + "Suite".ljust(width) + "".join(title.rjust(w) for _, title, w in _COLUMNS) + "Time".rjust(9)
        lines = [self.rule("Summary"), "", self.style(header, "dim")]

        def cells(row, bold=False):
            text = ""
            for status, _, w in _COLUMNS:
                value = row[status]
                cell = str(value) if value else "·"
                styled = self.style(cell, _STYLE_OF[status], *(("bold",) if bold else ())) if value else \
                    self.style(cell, "dim")
                text += " " * (w - len(cell)) + styled
            return text

        for (suite, row), label in zip(rows, labels):
            worst = "pass"
            for status in _SEVERITY + [TestCategory.CANCEL]:
                if row[status]:
                    worst = _STYLE_OF[status]
                    break
            lines.append("  {}{}{}".format(self.style(label, worst, "bold"), " " * (width - len(label)),
                                           cells(row) + "{:0.2f}s".format(suite.get_runtime() or 0).rjust(9)))
        table_width = width + sum(w for _, _, w in _COLUMNS) + 9
        lines.append("  " + self.style("─" * table_width, "dim"))
        worst = "pass"
        for status in _SEVERITY + [TestCategory.CANCEL]:
            if counts[status]:
                worst = _STYLE_OF[status]
                break
        lines.append("  {}{}{}{}".format(self.style("Total", worst, "bold"), " " * (width - 5), cells(counts, True),
                                         self.style("{:0.2f}s".format(runtime).rjust(9), "bold")))
        total = sum(counts.values())
        percents = "".join(("{}%".format(int(round(100.0 * counts[status] / total))) if counts[status] and total else "")
                           .rjust(w) for status, _, w in _COLUMNS)
        lines.append("  " + self.style(("{} test{}".format(total, "" if total == 1 else "s")).ljust(width) + percents,
                                       "dim"))
        lines.extend(["", self.style("─" * _RULE_WIDTH, "dim"), ""])
        return lines

    def __verdict(self, code, counts, runtime, errors):
        cli = bool(self.__cli)
        dot = self.style(" · ", "dim")
        if errors:
            text = "{}  {}".format(self.badge("FAILED", "err"), "run stopped by {}".format(type(errors[0]).__name__))
        elif self.__state.cancelled and self.__state.by_user:
            text = "{}  {}".format(self.badge("CANCELLED", "canc"), self.style("by Ctrl+C", "dim"))
        elif code:
            text = self.badge("FAILED", "err")
            if not (counts[TestCategory.FAIL] or counts[TestCategory.ERROR] or counts[TestCategory.IGNORE]):
                text += "  no tests ran"
        else:
            text = self.badge("PASSED", "pass")
        if self.__mode == "cli-quiet":
            parts = []
            for status, word in ((TestCategory.FAIL, "failed"), (TestCategory.ERROR, "error"),
                                 (TestCategory.IGNORE, "ignored")):
                if counts[status]:
                    parts.append(self.style("{} {}".format(counts[status], word), _STYLE_OF[status]))
            good = []
            for status, word in ((TestCategory.SUCCESS, "passed"), (TestCategory.SKIP, "skipped"),
                                 (TestCategory.CANCEL, "cancelled")):
                if counts[status]:
                    good.append(self.style("{} {}".format(counts[status], word), _STYLE_OF[status]))
            groups = [", ".join(parts)] if parts else []
            if good:
                groups.append(", ".join(good))
            groups.append("{:0.2f}s".format(runtime))
            text += "  " + dot.join(groups)
        if cli:
            joined = self.__mode == "cli-quiet" or (self.__state.cancelled and self.__state.by_user)
            text += (dot if joined else "  ") + self.style("exit code {}".format(code), "dim")
        return text
