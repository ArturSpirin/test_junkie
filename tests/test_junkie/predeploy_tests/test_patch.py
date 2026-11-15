from test_junkie.decorators import Suite, test
from tests.junkie_suites import patch_checks


@Suite()
class PatchSuite:

    @test(parameters=patch_checks.CHECKS)
    def patch(self, parameter):
        parameter()
