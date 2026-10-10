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
import os
import threading
import warnings

from test_junkie.errors import TestJunkieUsageError
from test_junkie.params import param_key
from test_junkie.views import META_LOCK

_LOCAL = threading.local()
_HERE = os.path.normcase(os.path.abspath(__file__))
_WARNED = set()  # call sites already warned about, one warning each
VALUE_LIMIT = 2000  # reports cut longer values to this many characters


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
