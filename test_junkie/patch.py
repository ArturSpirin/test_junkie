"""
Per-test patching with automatic undo: Patch.setattr / delattr / setitem / delitem / setenv / delenv.

Every change is stored on the running attempt's run context (see test_junkie.meta) and undone, last change first,
when the attempt ends, whatever its result: pass, fail, error, skip, cancel or a failed @beforeTest. A retry starts
from the original values. Call it from a @test(), a helper the test calls, @beforeTest, @afterTest, or a thread
wrapped with Meta.bind(fn).

Order: ON_SUCCESS / ON_FAILURE / ON_SKIP / ON_CANCEL listeners fire before the undo, so they still see the patched
values; @afterTest does too.

Patches are process-wide: an attribute or env var changed by one test is what every other thread sees until the
undo. Tests that patch the same thing must not run at the same time: use @test(parallelized=False) or a Limiter pool.
"""
import importlib
import inspect
import os
import threading

from test_junkie.errors import TestJunkieUsageError
from test_junkie.meta import current_context

_LOCK = threading.RLock()


class _NotSet(object):

    def __repr__(self):
        return "<notset>"


NOTSET = _NotSet()


def _resolve(dotted):
    """"pkg.module.attr" -> (the object that holds attr, "attr")"""
    if not isinstance(dotted, str) or "." not in dotted:
        raise TestJunkieUsageError("Patch: {!r} must be a dotted path like \"package.module.name\"".format(dotted))
    parts = dotted.split(".")
    holder = None
    for index in range(len(parts) - 1, 0, -1):
        try:
            holder = importlib.import_module(".".join(parts[:index]))
        except ImportError:
            continue
        for name in parts[index:-1]:
            try:
                holder = getattr(holder, name)
            except AttributeError:
                raise TestJunkieUsageError("Patch: {!r} has no {!r}".format(dotted, name))
        return holder, parts[-1]
    raise TestJunkieUsageError("Patch: can't import any module from {!r}".format(dotted))


def _context(call):
    context = current_context()
    if context is None:
        raise TestJunkieUsageError(
            "{call} needs a running test. Call it from a @test(), a helper the test calls, @beforeTest or "
            "@afterTest. In a thread the test starts itself, wrap the thread's function with Meta.bind(fn) "
            "first".format(call=call))
    if context.test is None:
        raise TestJunkieUsageError(
            "{call} was called in @beforeClass / @afterClass. Patches are undone after each test, so patch in "
            "@beforeTest or the test instead".format(call=call))
    return context


def _apply(call, change):
    """Run change() and store the undo it returns, unless this attempt's patches are already undone."""
    context = _context(call)
    with _LOCK:
        if context.patches_closed:
            raise TestJunkieUsageError(
                "{call} was called after its test ended and its patches were undone, so it would never be undone. "
                "A thread wrapped with Meta.bind(fn) must finish before its test does".format(call=call))
        undo = change()
        if undo is not None:
            context.patches.append(undo)


def undo_patches(context, close=True):
    """
    Undo the context's patches, last first. An undo that raises is logged and the rest still run.
    :param close: True when the attempt ends: later Patch.* calls on this context raise TestJunkieUsageError
    :return: the errors the undos raised
    """
    with _LOCK:
        undos = context.patches
        context.patches = []
        if close:
            context.patches_closed = True
    errors = []
    for undo in reversed(undos):
        try:
            undo()
        except Exception as error:
            from test_junkie.debugger import LogJunkie
            LogJunkie.error("Patch: an undo raised {!r}; the other patches were still undone".format(error),
                            exc_info=True)
            errors.append(error)
    return errors


class Patch(object):
    """Changes undone after the running test. Same names and arguments as pytest's monkeypatch."""

    @staticmethod
    def setattr(target, name, value=NOTSET, raising=True):
        """
        Patch.setattr(module_or_object, "name", value), or Patch.setattr("package.module.name", value)
        :param raising: when True (default), fail if the attribute doesn't exist yet
        """
        if value is NOTSET:
            value = name
            target, name = _resolve(target)

        def change():
            old = target.__dict__.get(name, NOTSET) if inspect.isclass(target) else getattr(target, name, NOTSET)
            if raising and not hasattr(target, name):
                raise AttributeError("{!r} has no attribute {!r}".format(target, name))
            setattr(target, name, value)

            def undo():
                if old is NOTSET:
                    delattr(target, name)
                else:
                    setattr(target, name, old)
            return undo
        _apply("Patch.setattr()", change)

    @staticmethod
    def delattr(target, name=NOTSET, raising=True):
        """
        Patch.delattr(module_or_object, "name"), or Patch.delattr("package.module.name")
        :param raising: when True (default), fail if the attribute doesn't exist
        """
        if name is NOTSET:
            target, name = _resolve(target)

        def change():
            if not hasattr(target, name):
                if raising:
                    raise AttributeError("{!r} has no attribute {!r}".format(target, name))
                return None
            old = target.__dict__.get(name, NOTSET) if inspect.isclass(target) else getattr(target, name)
            delattr(target, name)
            if old is NOTSET:  # inherited by a class: deleting it from the class removed nothing to restore
                return None
            return lambda: setattr(target, name, old)
        _apply("Patch.delattr()", change)

    @staticmethod
    def setitem(mapping, key, value):
        """mapping[key] = value, undone after the test"""
        def change():
            old = mapping[key] if key in mapping else NOTSET
            mapping[key] = value

            def undo():
                if old is NOTSET:
                    mapping.pop(key, None)
                else:
                    mapping[key] = old
            return undo
        _apply("Patch.setitem()", change)

    @staticmethod
    def delitem(mapping, key, raising=True):
        """
        del mapping[key], undone after the test
        :param raising: when True (default), fail if the key is missing
        """
        def change():
            if key not in mapping:
                if raising:
                    raise KeyError(key)
                return None
            old = mapping[key]
            del mapping[key]

            def undo():
                mapping[key] = old
            return undo
        _apply("Patch.delitem()", change)

    @staticmethod
    def setenv(name, value, prepend=None):
        """
        os.environ[name] = str(value), undone after the test
        :param prepend: a separator such as os.pathsep: put value in front of the current value instead
        """
        value = str(value)
        if prepend and name in os.environ:
            value = value + prepend + os.environ[name]
        Patch.setitem(os.environ, name, value)

    @staticmethod
    def delenv(name, raising=True):
        """
        Remove env var name, undone after the test
        :param raising: when True (default), fail if it isn't set
        """
        Patch.delitem(os.environ, name, raising=raising)

    @staticmethod
    def undo():
        """Undo this test's patches now; it can patch again after. The runner also undoes them when the test ends"""
        undo_patches(_context("Patch.undo()"), close=False)
