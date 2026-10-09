from test_junkie.decorators import Suite, test
from tests.junkie_suites import limiter_checks


@Suite()
class LimiterSuite:

    @test(parameters=limiter_checks.CHECKS)
    def limiter(self, parameter):
        parameter()
