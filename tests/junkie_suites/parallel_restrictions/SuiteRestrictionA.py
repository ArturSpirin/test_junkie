from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline
from tests.junkie_suites.parallel_restrictions.SuiteRestrictionB import SuiteRestrictionB


@Suite(pr=[SuiteRestrictionB])
class SuiteRestrictionA:

    @test()
    def a(self):
        timeline.record("suite_a")
