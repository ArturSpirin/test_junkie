from test_junkie.decorators import Suite, test


class _DummyClass:
    pass


def _dummy_fn():
    pass


# Suite whose pr= list contains a function (not a class) — triggers BadParameters
# in suite_qualifies() when suite multithreading is enabled.
@Suite(pr=[_dummy_fn])
class BadSuitePrSuite:

    @test()
    def test_a(self):
        pass


# Suite whose test pr= list contains a class (not a function) — triggers BadParameters
# in test_qualifies() on every run.
@Suite()
class BadTestPrSuite:

    @test(pr=[_DummyClass])
    def test_a(self):
        pass
