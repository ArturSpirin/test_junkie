from test_junkie.decorators import Suite, test
from tests.junkie_suites import conflict_checks


@Suite()
class ConflictsSuite:

    @test(parameters=conflict_checks.CHECKS)
    def conflicts(self, parameter):
        parameter()
