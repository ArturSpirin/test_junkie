from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline


@Suite()
class SuiteThrottleY:

    @test()
    def y(self):
        timeline.record("suite_throttle", duration=0.4)
