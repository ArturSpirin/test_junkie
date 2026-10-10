from test_junkie.decorators import Suite, test
from tests.junkie_suites import meta_checks


@Suite()
class MetaSuite:

    @test(parameters=meta_checks.CHECKS)
    def meta(self, parameter):
        parameter()
