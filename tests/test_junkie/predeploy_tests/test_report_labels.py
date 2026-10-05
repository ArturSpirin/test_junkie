from test_junkie.decorators import Suite, test
from tests.junkie_suites import ReportLabelSuite


@Suite()
class ReportLabelsTestSuite:

    @test()
    def report_labels_and_escaping(self):
        ReportLabelSuite.run_checks()
