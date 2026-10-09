import glob
import os

import pytest

from test_junkie.cli.cli_config import Config
from test_junkie.debugger import LogJunkie
from test_junkie.runner import Runner
from tests.junkie_suites.ReportFailureSuite import ReportFailureSuite


def _unwritable(tmp_path, name):
    # missing folders are created now, so a bad path needs a folder that can't exist: one under a file
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    return str(blocker / name)


def test_resource_monitor_temp_file_cleaned_up_even_if_html_report_fails(tmp_path):
    # cleanup() used to only run after report generation, so a bad report path leaked the temp file
    before = set(glob.glob(os.path.join(Config.get_root_dir(), ".resources_*")))

    bad_html_path = _unwritable(tmp_path, "report.html")
    with pytest.raises(Exception):
        Runner([ReportFailureSuite]).run(monitor_resources=True, html_report=bad_html_path)

    after = set(glob.glob(os.path.join(Config.get_root_dir(), ".resources_*")))
    assert after == before  # no leftover temp file from this run


def test_bad_xml_report_path_warns_on_stderr_by_default(tmp_path, capsys):
    # a bad xml_report path used to fail silently unless LogJunkie was explicitly enabled
    LogJunkie.disable_logging()  # confirm default state regardless of test order

    bad_xml_path = _unwritable(tmp_path, "report.xml")
    Runner([ReportFailureSuite]).run(xml_report=bad_xml_path)  # must not raise

    captured = capsys.readouterr()
    assert "Failed to write XML report" in captured.err
