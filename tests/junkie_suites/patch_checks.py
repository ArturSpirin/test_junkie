"""
Checks for test_junkie.patch.Patch (G4). Run by both test paths:
tests/pytest/predeploy_tests/test_patch.py and tests/test_junkie/predeploy_tests/test_patch.py.
On the TJ path a check runs inside the outer run's test, so "no test running" is checked in a fresh thread, which
carries no run context. Every inner run must leave patch_target, its env var and the caller's run context as they were
"""
import contextlib
import io
import os
import threading

from test_junkie.decorators import Suite, test, beforeTest, afterTest, beforeClass
from test_junkie.errors import TestJunkieUsageError
from test_junkie.listener import Listener
from test_junkie.meta import Meta, current_context
from test_junkie.objects import Limiter
from test_junkie.patch import Patch
from test_junkie.shortcuts import skip
from tests.junkie_suites import patch_target

SEEN = {}
POOL = "tj_patch_pool"


def _snapshot():
    return patch_target.VALUE, os.environ.get(patch_target.ENV), dict(patch_target.MAPPING)


ORIGINAL = ("original", None, {"key": "original"})


def _patch_all(tag):
    Patch.setattr(patch_target, "VALUE", tag)
    Patch.setenv(patch_target.ENV, tag)
    Patch.setitem(patch_target.MAPPING, "key", tag)


def _run(suites, **kwargs):
    from test_junkie.runner import Runner
    os.environ.pop(patch_target.ENV, None)
    before = current_context()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        Runner(suites).run(**kwargs)
    assert current_context() is before, "the inner run changed the caller's run context"
    assert _snapshot() == ORIGINAL, "a patch outlived its test: {}".format(_snapshot())


class SeesPatches(Listener):
    """Records what each event sees: listeners fire before the undo, so they see the patched values"""

    def __record(self, event, kwargs):
        name = kwargs["properties"]["jm"]["jto"].get_function_name()
        SEEN.setdefault("events", []).append((event, name, _snapshot()))

    def on_success(self, **kwargs):
        self.__record("success", kwargs)

    def on_failure(self, **kwargs):
        self.__record("failure", kwargs)

    def on_error(self, **kwargs):
        self.__record("error", kwargs)

    def on_skip(self, **kwargs):
        self.__record("skip", kwargs)


@Suite(listener=SeesPatches)
class EveryResultSuite:

    @test()
    def passes(self):
        _patch_all("passes")

    @test()
    def fails(self):
        _patch_all("fails")
        assert False

    @test()
    def errors(self):
        _patch_all("errors")
        raise RuntimeError("boom")

    @test()
    def skips(self):
        _patch_all("skips")
        skip("runtime skip")


@Suite(listener=SeesPatches)
class BeforeTestFailsSuite:

    @beforeTest()
    def before(self):
        _patch_all("before")
        raise RuntimeError("beforeTest fails")

    @test()
    def never_runs(self):
        SEEN["ran"] = True


@Suite()
class RetrySuite:

    @test(retry=2)
    def flaky(self):
        SEEN.setdefault("attempts", []).append(_snapshot())
        _patch_all("attempt")
        assert len(SEEN["attempts"]) > 1


@Suite()
class AfterTestSuite:

    @afterTest()
    def after(self):
        SEEN["after"] = _snapshot()

    @test()
    def patches(self):
        _patch_all("patched")


@Suite()
class ShapesSuite:

    @test()
    def lifo_and_shapes(self):
        Patch.setattr(patch_target, "VALUE", "first")
        Patch.setattr(patch_target, "VALUE", "second")
        Patch.setattr("tests.junkie_suites.patch_target.VALUE", "dotted")
        Patch.setattr(patch_target, "NEW_NAME", 1, raising=False)
        Patch.setattr(patch_target.Child, "kind", staticmethod(lambda: "child"))
        Patch.setattr(patch_target.Holder, "kind", staticmethod(lambda: "patched"))
        Patch.delitem(patch_target.MAPPING, "key")
        Patch.delitem(patch_target.MAPPING, "missing", raising=False)
        Patch.delenv(patch_target.ENV, raising=False)
        Patch.setenv(patch_target.ENV, 5)
        Patch.setenv(patch_target.ENV, "front", prepend=os.pathsep)
        SEEN["during"] = (patch_target.VALUE, patch_target.NEW_NAME, patch_target.Child.kind(),
                          patch_target.Holder.kind(), dict(patch_target.MAPPING), os.environ[patch_target.ENV])
        for call in (lambda: Patch.setattr(patch_target, "NOT_THERE", 1),
                     lambda: Patch.delattr(patch_target, "NOT_THERE"),
                     lambda: Patch.delitem(patch_target.MAPPING, "missing"),
                     lambda: Patch.delenv("TJ_PATCH_NEVER_SET")):
            try:
                call()
                SEEN.setdefault("raised", []).append(None)
            except (AttributeError, KeyError) as error:
                SEEN.setdefault("raised", []).append(type(error).__name__)

    @test()
    def delattr_and_undo_now(self):
        Patch.delattr(patch_target, "VALUE")
        SEEN["deleted"] = hasattr(patch_target, "VALUE")
        Patch.undo()
        SEEN["after_undo"] = patch_target.VALUE
        Patch.setattr(patch_target, "VALUE", "again")  # still patchable after Patch.undo()
        SEEN["again"] = patch_target.VALUE


@Suite()
class ClassHookSuite:

    @beforeClass()
    def before_class(self):
        try:
            Patch.setattr(patch_target, "VALUE", "class hook")
        except TestJunkieUsageError as error:
            SEEN["class_hook"] = str(error)

    @test()
    def runs(self):
        pass


@Suite()
class LateBindSuite:

    @test()
    def leaves_a_bound_function(self):
        SEEN["late"] = Meta.bind(lambda: Patch.setattr(patch_target, "VALUE", "late"))


class FussyDict(dict):
    """Its undo raises: __setitem__ fails once `fail` is set"""
    fail = False

    def __setitem__(self, key, value):
        if self.fail:
            raise RuntimeError("fussy undo")
        dict.__setitem__(self, key, value)


FUSSY = FussyDict(key="original")


@Suite()
class UndoRaisesSuite:

    @test(uses=POOL)
    def undo_raises(self):
        Patch.setattr(patch_target, "VALUE", "before fussy")
        Patch.setitem(FUSSY, "key", "patched")
        Patch.setenv(patch_target.ENV, "after fussy")
        FUSSY.fail = True

    @test(uses=POOL)
    def next_in_pool(self):
        SEEN["in_use"] = Limiter.get_pools()[POOL]["in_use"]
        SEEN["next_context"] = current_context().test.get_function_name()
        SEEN["next_sees"] = _snapshot()


def undone_after_pass_fail_error_and_skip():
    SEEN.clear()
    _run([EveryResultSuite])
    events = {name: (event, seen) for event, name, seen in SEEN["events"]}
    for name, event in (("passes", "success"), ("fails", "failure"), ("errors", "error"), ("skips", "skip")):
        assert events[name] == (event, (name, name, {"key": name})), events


def listeners_fire_before_the_undo():
    # pins the order: each listener above saw its own test's patches, not the originals
    SEEN.clear()
    _run([EveryResultSuite])
    assert all(seen != ORIGINAL for _, _, seen in SEEN["events"]), SEEN["events"]


def undone_when_before_test_fails():
    SEEN.clear()
    _run([BeforeTestFailsSuite])
    assert "ran" not in SEEN
    assert SEEN["events"][0][2] == ("before", "before", {"key": "before"}), SEEN["events"]


def a_retry_starts_from_the_originals():
    SEEN.clear()
    _run([RetrySuite])
    assert SEEN["attempts"] == [ORIGINAL, ORIGINAL], SEEN["attempts"]


def after_test_sees_the_patches():
    SEEN.clear()
    _run([AfterTestSuite])
    assert SEEN["after"] == ("patched", "patched", {"key": "patched"}), SEEN["after"]


def undone_last_first_for_every_shape():
    SEEN.clear()
    _run([ShapesSuite])
    assert SEEN["during"] == ("dotted", 1, "child", "patched", {}, "front" + os.pathsep + "5"), SEEN["during"]
    assert SEEN["raised"] == ["AttributeError", "AttributeError", "KeyError", "KeyError"], SEEN["raised"]
    assert not hasattr(patch_target, "NEW_NAME")
    assert "kind" not in patch_target.Child.__dict__
    assert patch_target.Holder.kind() == "original" and patch_target.Child.kind() == "original"
    assert SEEN["deleted"] is False and SEEN["after_undo"] == "original" and SEEN["again"] == "again"


def class_hooks_and_threads_without_a_test_cannot_patch():
    SEEN.clear()
    _run([ClassHookSuite])
    assert "@beforeClass" in SEEN["class_hook"], SEEN

    def outside():
        try:
            Patch.setenv(patch_target.ENV, "outside")
        except TestJunkieUsageError as error:
            SEEN["outside"] = str(error)
    thread = threading.Thread(target=outside)
    thread.start()
    thread.join()
    assert "needs a running test" in SEEN["outside"], SEEN
    assert os.environ.get(patch_target.ENV) is None


def a_patch_after_the_undo_raises():
    SEEN.clear()
    _run([LateBindSuite])
    try:
        SEEN["late"]()
    except TestJunkieUsageError as error:
        assert "after its test ended" in str(error), error
    else:
        raise AssertionError("a Patch.* call after its test's undo must raise TestJunkieUsageError")
    assert patch_target.VALUE == "original"


def an_undo_that_raises_still_releases_context_and_pool():
    SEEN.clear()
    FUSSY.fail = False
    dict.__setitem__(FUSSY, "key", "original")
    Limiter.pool(POOL, max_concurrent=2)
    try:
        _run([UndoRaisesSuite])  # also asserts VALUE and the env var were undone around the raising undo
        assert FUSSY["key"] == "patched"  # its own undo raised
        assert SEEN["in_use"] == 1, "the raising test kept its pool slot: in_use={}".format(SEEN["in_use"])
        assert SEEN["next_context"] == "next_in_pool"
        assert SEEN["next_sees"] == ORIGINAL, SEEN["next_sees"]
        assert Limiter.get_pools()[POOL]["in_use"] == 0
    finally:
        FUSSY.fail = False
        Limiter.remove_pools(POOL)


CHECKS = [undone_after_pass_fail_error_and_skip, listeners_fire_before_the_undo, undone_when_before_test_fails,
          a_retry_starts_from_the_originals, after_test_sees_the_patches, undone_last_first_for_every_shape,
          class_hooks_and_threads_without_a_test_cannot_patch, a_patch_after_the_undo_raises,
          an_undo_that_raises_still_releases_context_and_pool]
