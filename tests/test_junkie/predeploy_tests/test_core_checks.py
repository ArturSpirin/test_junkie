from test_junkie.decorators import Suite, test
from tests.junkie_suites import core_checks


@Suite()
class CoreChecksSuite:

    @test(parameters=core_checks.CHECKS)
    def core(self, parameter):
        parameter()
