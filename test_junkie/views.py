import copy
import threading

# held while copying a test's definition, so a copy never sees a half-done Meta.update
META_LOCK = threading.RLock()

_GETTERS = ("get_", "is_", "accepts_", "skip_", "parallelized")


def _copy(value):
    # metrics can change in other threads while being copied; try again rather than fail the hook
    for _ in range(3):
        try:
            return copy.deepcopy(value)
        except RuntimeError:
            continue
    return copy.copy(value)


def _kind(view):
    return type(view).__name__  # the view's own type; __class__ reports the live object's


class _ReadOnlyView(object):
    """
    Read-only window onto a live TestJunkie object, handed to hooks and Rules.
    Getters return copies, and anything assigned stays on the view, so nothing a hook does can change the run.
    """

    def __init__(self, live):
        object.__setattr__(self, "_live", live)
        object.__setattr__(self, "_local", {})

    @property
    def __class__(self):
        # isinstance(view, TestObject) keeps passing, as it did when hooks got a deep copy
        return type(object.__getattribute__(self, "_live"))

    def __getattr__(self, name):
        local = object.__getattribute__(self, "_local")
        if name in local:
            return local[name]
        if name.startswith("_"):
            raise AttributeError(name)
        live = object.__getattribute__(self, "_live")
        value = getattr(live, name)
        if callable(value):
            if not name.startswith(_GETTERS):
                raise AttributeError("'{}' is not available on {}: hooks get a read-only view, so only getters "
                                     "(get_*, is_*, accepts_*) can be called".format(name, _kind(self)))

            def getter(*args, **kwargs):
                with META_LOCK:
                    return _copy(value(*args, **kwargs))
            return getter
        return self._wrap(name, value)

    def _wrap(self, name, value):
        with META_LOCK:
            return _copy(value)

    def __setattr__(self, name, value):
        object.__getattribute__(self, "_local")[name] = value

    def __delattr__(self, name):
        object.__getattribute__(self, "_local").pop(name, None)

    def __repr__(self):
        return "<{} of {!r}>".format(_kind(self), object.__getattribute__(self, "_live"))


class SuiteView(_ReadOnlyView):
    """Read-only view of a SuiteObject."""

    def get_class_object(self):
        # the user's own class, not a copy: class attributes are the documented way to share state
        return object.__getattribute__(self, "_live").get_class_object()

    def get_class_instance(self):
        return object.__getattribute__(self, "_live").get_class_instance()


class TestView(_ReadOnlyView):
    """
    Read-only view of a TestObject, passed to @beforeTest / @afterTest hooks that declare a `test` argument,
    and to Rules.before_test / after_test.
    """

    def get_parameters(self, process_functions=False):
        # never runs a parameters function from a hook: that is the runner's job, once
        with META_LOCK:
            return _copy(object.__getattribute__(self, "_live").get_parameters(process_functions=False))

    def get_function_object(self):
        return object.__getattribute__(self, "_live").get_function_object()

    def _wrap(self, name, value):
        if name == "suite":
            return SuiteView(value)
        return _ReadOnlyView._wrap(self, name, value)
