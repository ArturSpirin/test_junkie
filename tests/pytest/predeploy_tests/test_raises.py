"""
Coverage for shortcuts.raises().

Covered:
  - expected type is swallowed, .value and .type expose it
  - a tuple of types, a subclass of the expected type
  - match: regex hit passes, miss fails, compiled pattern works
  - nothing raised, wrong type, match miss: AssertionError (FAIL, not ERROR), wrong type chained from the original
  - skip() inside the block still skips, even inside raises(Exception); raises(SkipTest) catches it
  - KeyboardInterrupt passes through
  - TypeError on a non-exception argument, AttributeError on .value before the block ends
  - test status via Runner: SUCCESS / FAIL with 0 ERROR / SKIP
"""
import re

from test_junkie.constants import TestCategory
from test_junkie.errors import SkipTest
from test_junkie.runner import Runner
from test_junkie.shortcuts import raises, skip, Raised

from tests.junkie_suites.raises.RaisesSuites import (
    RaisesExpectedSuite,
    RaisesNothingSuite,
    RaisesWrongTypeSuite,
    RaisesNoMatchSuite,
    RaisesSkipInsideSuite,
)


def _assertion_from(block):
    try:
        block()
    except AssertionError as e:
        return e
    raise Exception("AssertionError was not raised")


# ── direct behaviour ─────────────────────────────────────────────────────────

def test_raises_returns_raised_with_value_and_type():
    with raises(ValueError) as caught:
        raise ValueError("bad id x")
    assert isinstance(caught, Raised)
    assert caught.value.args == ("bad id x",)
    assert caught.type is ValueError


def test_raises_accepts_tuple_and_subclass():
    with raises((KeyError, ValueError)) as caught:
        raise KeyError("k")
    assert caught.type is KeyError
    with raises(LookupError) as caught:
        raise IndexError("i")
    assert caught.type is IndexError


def test_raises_match_hit():
    with raises(ValueError, match=r"bad id \w") as caught:
        raise ValueError("bad id x")
    assert caught.type is ValueError
    with raises(ValueError, match=re.compile("^bad")):
        raise ValueError("bad id x")


def test_raises_match_miss_fails_with_repr():
    def block():
        with raises(ValueError, match=r"bad id"):
            raise ValueError("line one\nline two")
    error = _assertion_from(block)
    assert str(error) == "ValueError message 'line one\\nline two' does not match 'bad id'"
    assert isinstance(error.__cause__, ValueError)


def test_raises_nothing_fails():
    def block():
        with raises((ValueError, KeyError)):
            pass
    assert str(_assertion_from(block)) == "DID NOT RAISE ValueError or KeyError"


def test_raises_wrong_type_fails_chained():
    original = KeyError("k")

    def block():
        with raises(ValueError):
            raise original
    error = _assertion_from(block)
    assert str(error) == "expected ValueError, got KeyError: 'k'"
    assert error.__cause__ is original


def test_raises_skip_passes_through():
    for expected in (ValueError, Exception):
        try:
            with raises(expected):
                skip("not configured")
        except SkipTest as e:
            assert e.reason == "not configured"
        else:
            raise Exception("SkipTest was swallowed by raises({})".format(expected.__name__))


def test_raises_skiptest_listed_is_caught():
    with raises(SkipTest) as caught:
        skip("why")
    assert caught.value.reason == "why"


def test_raises_keyboard_interrupt_passes_through():
    try:
        with raises(Exception):
            raise KeyboardInterrupt()
    except KeyboardInterrupt:
        return
    raise Exception("KeyboardInterrupt was swallowed")


def test_raises_rejects_non_exception():
    for bad in ("ValueError", ValueError("x"), (), (ValueError, int)):
        try:
            raises(bad)
        except TypeError:
            continue
        raise Exception("TypeError not raised for {!r}".format(bad))


def test_raises_value_before_exit():
    with raises(ValueError) as caught:
        try:
            caught.value
        except AttributeError:
            raise ValueError("read too early")
    assert str(caught.value) == "read too early"


# ── status via Runner ────────────────────────────────────────────────────────

def test_raises_expected_is_success():
    report = Runner([RaisesExpectedSuite]).run().get_basic_report()["tests"]
    assert report[TestCategory.SUCCESS] == 2
    assert report[TestCategory.FAIL] == 0
    assert report[TestCategory.ERROR] == 0


def test_raises_failures_are_fail_not_error():
    for suite in (RaisesNothingSuite, RaisesWrongTypeSuite, RaisesNoMatchSuite):
        report = Runner([suite]).run().get_basic_report()["tests"]
        assert report[TestCategory.FAIL] == 1, suite.__name__
        assert report[TestCategory.ERROR] == 0, suite.__name__


def test_raises_skip_inside_is_skip():
    report = Runner([RaisesSkipInsideSuite]).run().get_basic_report()["tests"]
    assert report[TestCategory.SKIP] == 2
    assert report[TestCategory.SUCCESS] == 0
    assert report[TestCategory.FAIL] == 0
