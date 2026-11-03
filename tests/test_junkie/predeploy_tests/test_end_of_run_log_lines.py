import os
import tempfile

from test_junkie.decorators import Suite, test
from tests.junkie_suites.EndOfRunLogSuites import end_of_run_lines, check_lines


@Suite()
class EndOfRunLogLinesTestSuite:

    @test()
    def each_end_of_run_step_logs_timed_start_and_finish_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            lines = end_of_run_lines(html_report=os.path.join(folder, "report.html"),
                                     xml_report=os.path.join(folder, "report.xml"),
                                     json_report=os.path.join(folder, "report.json"))
        check_lines(lines, ["aggregator", "console summary", "HTML report", "XML report", "JSON report"])

    @test()
    def reports_not_requested_log_nothing(self):
        lines = end_of_run_lines()
        check_lines(lines, ["aggregator", "console summary"])
