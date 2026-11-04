from test_junkie.decorators import Suite, test
from tests.junkie_suites import stress_checks


@Suite()
class StressHarnessSuite:

    @test(parameters=stress_checks.CHECKS)
    def stress_harness(self, parameter):
        parameter()

    # large stress sizes run on demand: set TJ_STRESS_LARGE=1
    @test(parameters=stress_checks.LARGE_CHECKS, skip=not stress_checks.LARGE_ENABLED)
    def stress_budget_large(self, parameter):
        parameter()
