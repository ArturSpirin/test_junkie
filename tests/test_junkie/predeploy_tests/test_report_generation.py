import glob
import io
import os
import sys
import tempfile

from test_junkie.cli.cli_config import Config
from test_junkie.debugger import LogJunkie
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.junkie_suites.ReportFailureSuite import ReportFailureSuite


@Suite()
class ReportGenerationFailureTestSuite:

    @test()
    def resource_monitor_temp_file_cleaned_up_even_if_html_report_fails(self):
        before = set(glob.glob(os.path.join(Config.get_root_dir(), ".resources_*")))
        tmp_dir = tempfile.mkdtemp()
        bad_html_path = os.path.join(tmp_dir, "does", "not", "exist", "report.html")
        raised = False
        try:
            Runner([ReportFailureSuite]).run(monitor_resources=True, html_report=bad_html_path)
        except Exception:
            raised = True
        assert raised
        after = set(glob.glob(os.path.join(Config.get_root_dir(), ".resources_*")))
        assert after == before

    @test()
    def bad_xml_report_path_warns_on_stderr_by_default(self):
        LogJunkie.disable_logging()
        tmp_dir = tempfile.mkdtemp()
        bad_xml_path = os.path.join(tmp_dir, "does", "not", "exist", "report.xml")
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        try:
            Runner([ReportFailureSuite]).run(xml_report=bad_xml_path)
            captured = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        assert "Failed to write XML report" in captured
