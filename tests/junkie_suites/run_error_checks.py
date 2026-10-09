"""
When a run fails (here: a broken listener), run() still raises - but only after the console summary and the HTML/XML
reports are written. Before 0.9a5 it raised first, so a threaded run with a failing listener ran every test and then
produced no summary and no reports. Since 0.9a8 a listener error no longer stops the run, see listener_error_checks.py.
Shared by the pytest and TJ test paths.
"""
import contextlib
import io
import os
import shutil
import tempfile

from test_junkie.errors import TestListenerError
from test_junkie.runner import Runner
from tests.junkie_suites.parallel_restrictions.BrokenListener import BrokenListenerSuite


def _run_and_expect_reports(**run_kwargs):
    folder = tempfile.mkdtemp()
    html, xml = os.path.join(folder, "report.html"), os.path.join(folder, "report.xml")
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            try:
                Runner([BrokenListenerSuite], html_report=html, xml_report=xml).run(**run_kwargs)
                raise AssertionError("expected TestListenerError ({})".format(run_kwargs))
            except TestListenerError:
                pass
        assert "Summary" in out.getvalue() and "1 listener call failed" in out.getvalue(),             out.getvalue()[-500:]
        assert os.path.isfile(xml) and "BrokenListenerSuite" in open(xml).read()
        with io.open(html, encoding="utf-8") as report:
            assert "BrokenListenerSuite" in report.read()
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def reports_written_when_main_thread_errors():
    _run_and_expect_reports()


def reports_written_when_suite_thread_errors():
    _run_and_expect_reports(suite_multithreading_limit=2)


def reports_written_when_test_thread_errors():
    _run_and_expect_reports(test_multithreading_limit=2)


CHECKS = [reports_written_when_main_thread_errors, reports_written_when_suite_thread_errors,
          reports_written_when_test_thread_errors]
