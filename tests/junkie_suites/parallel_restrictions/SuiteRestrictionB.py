from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline


@Suite()
class SuiteRestrictionB:

    @test()
    def b(self):
        timeline.record("suite_b", duration=0.6)
