from test_junkie.decorators import Suite, test
from tests.junkie_suites import exclusive_checks


@Suite()
class ExclusiveTestsSuite:

    @test(parameters=exclusive_checks.CHECKS)
    def exclusive_tests(self, parameter):
        parameter()
