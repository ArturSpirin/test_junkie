from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline


@Suite()
class TestRestrictionSuite:

    @test()
    def m(self):
        timeline.record("test_m")

    @test(pr=[m])
    def n(self):
        timeline.record("test_n")
