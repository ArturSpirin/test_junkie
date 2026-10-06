from test_junkie.decorators import Suite, test
from tests.junkie_suites import analyzer_samples


@Suite()
class AnalyzerSuite:

    @test()
    def report_insights(self):
        analyzer_samples.run_checks()
