from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline


@Suite()
class SuiteThrottleZ:

    @test()
    def z(self):
        timeline.record("suite_throttle", duration=0.4)
