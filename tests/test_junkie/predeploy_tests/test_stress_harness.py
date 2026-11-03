from test_junkie.decorators import Suite, test
from tests.junkie_suites import stress_checks


@Suite()
class StressHarnessSuite:

    @test(parameters=stress_checks.CHECKS)
    def stress_harness(self, parameter):
        parameter()
