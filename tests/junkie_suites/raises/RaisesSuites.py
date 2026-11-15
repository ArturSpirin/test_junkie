from test_junkie.decorators import Suite, test
from test_junkie.shortcuts import raises, skip


@Suite()
class RaisesExpectedSuite:

    @test()
    def raises_expected(self):
        with raises(ValueError):
            raise ValueError("bad id x")

    @test()
    def raises_expected_with_match(self):
        with raises(ValueError, match=r"bad id"):
            raise ValueError("bad id x")


@Suite()
class RaisesNothingSuite:

    @test()
    def raises_nothing(self):
        with raises(ValueError):
            pass


@Suite()
class RaisesWrongTypeSuite:

    @test()
    def raises_wrong_type(self):
        with raises(ValueError):
            raise KeyError("k")


@Suite()
class RaisesNoMatchSuite:

    @test()
    def raises_no_match(self):
        with raises(ValueError, match=r"bad id"):
            raise ValueError("something else")


@Suite()
class RaisesSkipInsideSuite:

    @test()
    def skip_inside_raises(self):
        with raises(ValueError):
            skip("not configured")

    @test()
    def skip_inside_raises_exception(self):
        with raises(Exception):
            skip("not configured")
