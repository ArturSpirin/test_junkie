"""
Test metadata: declared with @test(meta=meta(...)), changed while a test runs with Meta.update().

Each thread that runs a test attempt carries a run context (suite, test, parameter, suite parameter, attempt), set
by the runner around @beforeTest -> test -> @afterTest and cleared after. Meta.update(**values) writes to the test
that context names, so it works from the test, any helper it calls, @beforeTest and @afterTest. Meta.bind(fn)
carries the context into threads the test starts itself. @beforeClass / @afterClass get a suite-level context:
Meta.suite.update(**values) writes suite meta for that suite parameter there.

The old call, Meta.update(self, parameter=..., suite_parameter=..., **values), still writes to exactly the slot it
names (missing parameters included, never filled in), finds the test the old way (the run context, then the call
stack) and warns instead of failing when it can't land.
"""
import functools
import inspect
import json
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import warnings

from test_junkie.errors import TestJunkieUsageError
from test_junkie.params import param_key
from test_junkie.views import META_LOCK

_LOCAL = threading.local()
_HERE = os.path.normcase(os.path.abspath(__file__))
_WARNED = set()  # call sites already warned about, one warning each
VALUE_LIMIT = 2000  # reports cut longer values to this many characters
LINKS_KEY = "links"  # Meta.link() adds to this list
ATTACHMENTS_KEY = "attachments"  # Meta.attach() adds to this list
ATTACH_EMBED_LIMIT = 512 * 1024  # the HTML report embeds attachments up to this size, links bigger ones
_ATTACH_DIR = None
_ATTACH_COUNT = 0


def meta(**kwargs):
    """
    Use this function in order to define metadata for a @test().
    aka @test(meta=meta(name="Example Name", expected="...", ...))
    :param kwargs: key/value pairs
    :return: Dictionary
    """
    return kwargs


class TestJunkieMetaWarning(UserWarning):
    """An old-style Meta.update() call whose values went somewhere other than the running test, or nowhere."""


class RunContext(object):

    __slots__ = ("suite", "test", "parameter", "class_parameter", "attempt")

    def __init__(self, suite, test=None, parameter=None, class_parameter=None, attempt=None):
        self.suite = suite
        self.test = test  # None in @beforeClass / @afterClass
        self.parameter = parameter
        self.class_parameter = class_parameter
        self.attempt = attempt


def current_context():
    return getattr(_LOCAL, "context", None)


def enter_context(context):
    """:return: the context this replaced, for leave_context()"""
    previous = current_context()
    _LOCAL.context = context
    return previous


def leave_context(previous):
    _LOCAL.context = previous


def _attachment_dir():
    """One folder per process for attachment copies, made on first use"""
    global _ATTACH_DIR
    with META_LOCK:
        if _ATTACH_DIR is None or not os.path.isdir(_ATTACH_DIR):
            _ATTACH_DIR = tempfile.mkdtemp(prefix="test_junkie_attachments_")
        return _ATTACH_DIR


def _save_attachment(name, content, mime=None):
    global _ATTACH_COUNT
    name = str(name)
    source = None
    if isinstance(content, (bytes, bytearray, memoryview)):
        data = bytes(content)
    elif isinstance(content, (str, os.PathLike)):
        source = os.path.abspath(os.fspath(content))
        if not os.path.isfile(source):
            raise TestJunkieUsageError(
                "Meta.attach({!r}, ...): {} is not a file. Pass bytes for content you have in memory "
                "(text: \"...\".encode())".format(name, source))
        data = None
    else:
        raise TestJunkieUsageError("Meta.attach({!r}, ...) takes bytes or a file path, got {}"
                                   .format(name, type(content).__name__))
    folder = _attachment_dir()
    with META_LOCK:
        _ATTACH_COUNT += 1
        number = _ATTACH_COUNT
    safe = re.sub(r"[^\w.\-]+", "_", os.path.basename(name)) or "attachment"
    path = os.path.join(folder, "{:05d}_{}".format(number, safe))
    if data is None:
        shutil.copyfile(source, path)
    else:
        with open(path, "wb") as target:
            target.write(data)
    mime = mime or mimetypes.guess_type(name)[0] or (source and mimetypes.guess_type(source)[0]) \
        or "application/octet-stream"
    return {"name": name, "size": os.path.getsize(path), "mime": mime, "path": path, "source": source}


def report_value(value, limit=VALUE_LIMIT, _depth=0):
    """
    A JSON-safe copy of a meta value for reports: strings, numbers, booleans and None as they are, bytes decoded
    (bad bytes replaced), lists/tuples/sets as lists, dicts with string keys, anything else as str(). Strings longer
    than `limit` are cut with a note.
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        if limit and len(value) > limit:
            return value[:limit] + "… [cut {} characters]".format(len(value) - limit)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if _depth < 10:
        if isinstance(value, dict):
            return {str(k): report_value(v, limit, _depth + 1) for k, v in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [report_value(v, limit, _depth + 1) for v in value]
    try:
        text = str(value)
    except Exception:
        text = repr(value)
    return report_value(text, limit, _depth + 1)


def report_text(value, limit=VALUE_LIMIT):
    """report_value() as one string (JSON for anything that isn't a string), for XML attributes and the console."""
    safe = report_value(value, limit)
    return safe if isinstance(safe, str) else json.dumps(safe)


def _call_site():
    for frame_info in inspect.stack()[1:]:
        filename = os.path.normcase(os.path.abspath(frame_info.filename))
        if filename != _HERE and not filename.endswith(os.path.normcase(os.path.join("test_junkie", "decorators.py"))):
            return frame_info.filename, frame_info.lineno
    return "<unknown>", 0


def _warn_once(message):
    from test_junkie.debugger import LogJunkie
    filename, lineno = _call_site()
    with META_LOCK:
        if (filename, lineno) in _WARNED:
            return
        _WARNED.add((filename, lineno))
    LogJunkie.warn(message)
    warnings.warn_explicit(message, TestJunkieMetaWarning, filename, lineno)


def _require_test(call):
    context = current_context()
    if context is None:
        raise TestJunkieUsageError(
            "{call} needs a running test. Call it from a @test(), a helper the test calls, @beforeTest or "
            "@afterTest. In a thread the test starts itself, wrap the thread's function with Meta.bind(fn) first. "
            "For values that don't change, declare them instead: @test(meta=meta(...))".format(call=call))
    if context.test is None:
        raise TestJunkieUsageError(
            "{call} was called in @beforeClass / @afterClass, where no test is running yet. Use "
            "Meta.suite.update(...) for suite-level values there".format(call=call))
    return context


def _find_test(suite):
    """The TestObject an old-style call means: the running test if it's this suite's, else the call stack."""
    context = current_context()
    if context is not None and context.test is not None and suite.__class__ is context.suite.get_class_object():
        return context.test
    from test_junkie.builder import Builder
    for suite_object in Builder.get_execution_roster().values():
        if suite.__class__ == suite_object.get_class_object():
            for frame in inspect.stack():
                name = inspect.getframeinfo(frame[0]).function
                # only match this suite's actual test names, not just any attribute with that name
                if name in suite_object.get_test_function_names():
                    for test_object in suite_object.get_test_objects():
                        if test_object.get_function_name() == name:
                            return test_object
    return None


def _is_suite_instance(value):
    """True for an instance of a @Suite class, so Meta.update(suite=self, ...) (0.9a7's keyword form) is the old call"""
    if value is None or isinstance(value, (str, bytes, int, float, bool, list, tuple, dict, set)):
        return False
    context = current_context()
    if context is not None and context.suite is not None and value.__class__ is context.suite.get_class_object():
        return True
    from test_junkie.builder import Builder
    return any(value.__class__ == suite_object.get_class_object()
               for suite_object in Builder.get_execution_roster().values())


def _slot_label(parameter, class_parameter):
    return "parameter {}, suite parameter {}".format(
        "None" if parameter is None else param_key(parameter),
        "None" if class_parameter is None else param_key(class_parameter))


class _SuiteMeta(object):
    """Meta.suite: suite-level values, per suite parameter (listeners get them in properties["suite_meta"])."""

    @staticmethod
    def update(**values):
        context = current_context()
        if context is None:
            raise TestJunkieUsageError(
                "Meta.suite.update() needs a running suite: call it from @beforeClass, @afterClass, @beforeTest, "
                "@afterTest or a test")
        context.suite.update_runtime_meta(context.class_parameter, values)

    @staticmethod
    def get(key=None):
        context = current_context()
        if context is None:
            raise TestJunkieUsageError("Meta.suite.get() needs a running suite")
        values = context.suite.get_meta(copy_of_meta=True, class_parameter=context.class_parameter)
        return values if key is None else values.get(key)


class Meta(object):

    suite = _SuiteMeta()

    @staticmethod
    def update(*args, **values):
        """
        Meta.update(**values): set metadata on the running test, for its current parameter and suite parameter.
        Works in the test, helpers it calls, @beforeTest and @afterTest; in threads the test starts, use Meta.bind.

        Meta.update(self, parameter=None, suite_parameter=None, **values): the old call. Writes to exactly that
        parameter / suite parameter slot of the test (it doesn't fill in missing ones) and warns, once per call
        site, when that isn't the slot the test is running as, or when no running test was found.
        """
        if not args and _is_suite_instance(values.get("suite")):  # Meta.update(suite=self, ...)
            args = (values.pop("suite"),)
        if args:
            suite = args[0]
            parameter = args[1] if len(args) > 1 else values.pop("parameter", None)
            suite_parameter = args[2] if len(args) > 2 else values.pop("suite_parameter", None)
            return Meta.__update_slot(suite, parameter, suite_parameter, values)
        context = _require_test("Meta.update()")
        context.test.set_meta(context.parameter, context.class_parameter, values, context.attempt)

    @staticmethod
    def __update_slot(suite, parameter, suite_parameter, values):
        with META_LOCK:
            test = _find_test(suite)
            if test is None:
                _warn_once("Meta.update(self, ...) found no running test of {} to write to, so these values were "
                           "dropped: {}. Call it from a test (or @beforeTest/@afterTest), and pass the instance "
                           "(self), not the class".format(getattr(suite, "__name__", type(suite).__name__),
                                                          sorted(values)))
                return
            context = current_context()
            attempt = None
            if context is not None and context.test is test:
                running = (param_key(context.parameter), param_key(context.class_parameter))
                if (param_key(parameter), param_key(suite_parameter)) == running:
                    attempt = context.attempt
                else:
                    _warn_once("Meta.update(self, ...) wrote to {} of {}, but the test runs as {}. Pass the "
                               "running parameter= and suite_parameter=, or call Meta.update(**values) without "
                               "self, which always writes to the running test"
                               .format(_slot_label(parameter, suite_parameter), test,
                                       _slot_label(context.parameter, context.class_parameter)))
            test.set_meta(parameter, suite_parameter, values, attempt)

    @staticmethod
    def append(key, value):
        """
        Add a value to the list under `key` on the running test (created on first use), e.g. one line per step:
        Meta.append("steps", "opened the cart"). Across retries the list keeps growing; each attempt's record lists
        what that attempt added. Raises if `key` already holds something that isn't a list.
        """
        context = _require_test("Meta.append()")
        context.test.append_meta(context.parameter, context.class_parameter, key, [value], context.attempt)

    @staticmethod
    def link(label, url):
        """
        Add a link to the running test, shown clickable in the HTML report: Meta.link("Jira", "https://...").
        Stored in the metadata under "links" as a list of {"label": str, "url": str}. The same label and URL again
        (a retry, say) isn't listed twice.
        """
        context = _require_test("Meta.link()")
        context.test.append_meta(context.parameter, context.class_parameter, LINKS_KEY,
                                 [{"label": str(label), "url": str(url)}], context.attempt, call="Meta.link()",
                                 unique=True)

    @staticmethod
    def attach(name, content, mime=None):
        """
        Attach a file to the running test: Meta.attach("page.png", driver.get_screenshot_as_png()) or
        Meta.attach("server.log", "/var/log/app.log"). `content` is bytes (str text: encode it first) or a path to an
        existing file, which is copied right away, so later changes to it don't matter. The HTML report embeds files
        up to ATTACH_EMBED_LIMIT bytes and links bigger ones, saved next to it.
        Stored in the metadata under "attachments" as a list of
        {"name": str, "size": int (bytes), "mime": str, "path": str (the saved copy), "source": str|None (the path
        you passed)}.
        """
        context = _require_test("Meta.attach()")
        entry = _save_attachment(name, content, mime)
        context.test.append_meta(context.parameter, context.class_parameter, ATTACHMENTS_KEY, [entry],
                                 context.attempt, call="Meta.attach()")

    @staticmethod
    def get(key=None):
        """
        Read the running test's metadata (declared values plus what was set so far).
        :param key: one key, or None for a copy of all of it
        """
        context = _require_test("Meta.get()")
        values = context.test.get_meta(context.parameter, context.class_parameter, copy_of_meta=True)
        return values if key is None else values.get(key)

    @staticmethod
    def get_meta(*args, **kwargs):
        """
        Meta.get_meta("key"): same as Meta.get("key"), but returns None instead of raising outside a test.
        Meta.get_meta(self, parameter=None, suite_parameter=None): the old call, the live metadata of that slot.
        """
        if args and isinstance(args[0], str):
            try:
                return Meta.get(args[0])
            except TestJunkieUsageError:
                return None
        if not args and _is_suite_instance(kwargs.get("suite")):  # Meta.get_meta(suite=self, ...)
            args = (kwargs["suite"],)
        if not args:
            return Meta.get()
        suite = args[0]
        parameter = args[1] if len(args) > 1 else kwargs.get("parameter")
        suite_parameter = args[2] if len(args) > 2 else kwargs.get("suite_parameter")
        with META_LOCK:
            test = _find_test(suite)
            return None if test is None else test.get_meta(parameter, suite_parameter)

    @staticmethod
    def bind(fn):
        """
        Wrap a function that runs in a thread the test starts, so Meta.update() / Meta.get() inside it write to
        and read from this test: threading.Thread(target=Meta.bind(worker)).
        """
        context = current_context()
        if context is None:
            raise TestJunkieUsageError("Meta.bind() needs a running test: call it in the test (or a hook) before "
                                       "you start the thread")

        @functools.wraps(fn)
        def bound(*args, **kwargs):
            previous = enter_context(context)
            try:
                return fn(*args, **kwargs)
            finally:
                leave_context(previous)
        return bound
