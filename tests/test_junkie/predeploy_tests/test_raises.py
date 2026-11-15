import re

from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
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


@Suite()
class RaisesTestSuite:

    @test()
    def returns_raised_with_value_and_type(self):
        with raises(ValueError) as caught:
            raise ValueError("bad id x")
        assert isinstance(caught, Raised)
        assert caught.value.args == ("bad id x",)
        assert caught.type is ValueError

    @test()
    def accepts_tuple_and_subclass(self):
        with raises((KeyError, ValueError)) as caught:
            raise KeyError("k")
        assert caught.type is KeyError
        with raises(LookupError) as caught:
            raise IndexError("i")
        assert caught.type is IndexError

    @test()
    def match_hit(self):
        with raises(ValueError, match=r"bad id \w") as caught:
            raise ValueError("bad id x")
        assert caught.type is ValueError
        with raises(ValueError, match=re.compile("^bad")):
            raise ValueError("bad id x")

    @test()
    def match_miss_fails_with_repr(self):
        def block():
            with raises(ValueError, match=r"bad id"):
                raise ValueError("line one\nline two")
        error = _assertion_from(block)
        assert str(error) == "ValueError message 'line one\\nline two' does not match 'bad id'"
        assert isinstance(error.__cause__, ValueError)

    @test()
    def nothing_raised_fails(self):
        def block():
            with raises((ValueError, KeyError)):
                pass
        assert str(_assertion_from(block)) == "DID NOT RAISE ValueError or KeyError"

    @test()
    def wrong_type_fails_chained(self):
        original = KeyError("k")

        def block():
            with raises(ValueError):
                raise original
        error = _assertion_from(block)
        assert str(error) == "expected ValueError, got KeyError: 'k'"
        assert error.__cause__ is original

    @test()
    def skip_passes_through(self):
        for expected in (ValueError, Exception):
            try:
                with raises(expected):
                    skip("not configured")
            except SkipTest as e:
                assert e.reason == "not configured"
            else:
                raise Exception("SkipTest was swallowed by raises({})".format(expected.__name__))

    @test()
    def skiptest_listed_is_caught(self):
        with raises(SkipTest) as caught:
            skip("why")
        assert caught.value.reason == "why"

    @test()
    def keyboard_interrupt_passes_through(self):
        try:
            with raises(Exception):
                raise KeyboardInterrupt()
        except KeyboardInterrupt:
            return
        raise Exception("KeyboardInterrupt was swallowed")

    @test()
    def rejects_non_exception(self):
        for bad in ("ValueError", ValueError("x"), (), (ValueError, int)):
            try:
                raises(bad)
            except TypeError:
                continue
            raise Exception("TypeError not raised for {!r}".format(bad))

    @test()
    def value_before_exit(self):
        with raises(ValueError) as caught:
            try:
                caught.value
            except AttributeError:
                raise ValueError("read too early")
        assert str(caught.value) == "read too early"

    @test()
    def expected_is_success(self):
        report = Runner([RaisesExpectedSuite]).run().get_basic_report()["tests"]
        assert report[TestCategory.SUCCESS] == 2
        assert report[TestCategory.FAIL] == 0
        assert report[TestCategory.ERROR] == 0

    @test()
    def failures_are_fail_not_error(self):
        for suite in (RaisesNothingSuite, RaisesWrongTypeSuite, RaisesNoMatchSuite):
            report = Runner([suite]).run().get_basic_report()["tests"]
            assert report[TestCategory.FAIL] == 1, suite.__name__
            assert report[TestCategory.ERROR] == 0, suite.__name__

    @test()
    def skip_inside_is_skip(self):
        report = Runner([RaisesSkipInsideSuite]).run().get_basic_report()["tests"]
        assert report[TestCategory.SKIP] == 2
        assert report[TestCategory.SUCCESS] == 0
        assert report[TestCategory.FAIL] == 0
