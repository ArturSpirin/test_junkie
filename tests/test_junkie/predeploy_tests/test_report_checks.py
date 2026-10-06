from test_junkie.decorators import Suite, test
from tests.junkie_suites import report_checks


@Suite()
class ReportChecksSuite:

    @test(parameters=report_checks.CHECKS)
    def report(self, parameter):
        parameter()
