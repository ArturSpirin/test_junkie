from tests.junkie_suites.EndOfRunLogSuites import end_of_run_lines, check_lines


def test_each_end_of_run_step_logs_timed_start_and_finish_lines(tmp_path):
    lines = end_of_run_lines(html_report=str(tmp_path / "report.html"), xml_report=str(tmp_path / "report.xml"),
                             json_report=str(tmp_path / "report.json"))
    check_lines(lines, ["aggregator", "console summary", "HTML report", "XML report", "JSON report"])


def test_reports_not_requested_log_nothing():
    lines = end_of_run_lines()
    check_lines(lines, ["aggregator", "console summary"])
