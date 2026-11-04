"""
The end-of-run reports stay correct: the stress harness's small size (tests/stress/report_stress.py) checked with
tests/stress/report_check.py, on the pytest and TJ test paths. Generated data only.

One generated run per process, made on first use and only read by the checks. A check with `known_bug` fails today
because of that task's bug (pytest: xfail strict, TJ: skipped with the key); `needs_browser` checks need Playwright
and Chromium (see tests/stress/README.md) and are skipped without them.
"""
import atexit
import os
import shutil
import tempfile
import xml.etree.ElementTree as ElementTree

from tests.stress import report_check, report_stress

SIZE = {"tests": 40, "fail_rate": 0.3, "skip_rate": 0.1, "reruns": 2, "frames": 40}
_kept = []


def _report():
    """The folder with this process's generated run: report.xml, report.html, expected.json"""
    if not _kept:
        out = tempfile.mkdtemp(prefix="tj_report_check_")
        atexit.register(shutil.rmtree, out, True)
        result = report_stress.run_size(SIZE, out, passes=("time",), timeout=300)
        assert result["finished"], result
        _kept.append(out)
    return _kept[0]


def _expected():
    return report_check.expected(_report())


def xml_parses_with_a_standard_parser():
    root = ElementTree.parse(os.path.join(_report(), "report.xml")).getroot()
    assert len(list(root.iter("testcase"))) == SIZE["tests"]


def xml_test_and_rerun_counts_match():
    want, xml = _expected(), report_check.xml_counts(os.path.join(_report(), "report.xml"))
    assert xml["attributes"]["tests"] == xml["elements"]["tests"] == want["tests"], (xml, want)
    assert xml["attributes"]["passed"] == xml["elements"]["passed"] == want["passed"], (xml, want)
    assert xml["elements"]["reruns"] == want["reruns"] == 24, (xml, want)


def xml_failure_error_skip_counts_match():
    want, xml = _expected(), report_check.xml_counts(os.path.join(_report(), "report.xml"))
    for count in ("failures", "errors", "skipped"):
        assert xml["attributes"][count] == xml["elements"][count] == want[count], (count, xml, want)


def xml_validates_against_junit_10():
    result = report_check.validate_xml(os.path.join(_report(), "report.xml"))
    assert result["valid"], result["errors"]


def html_totals_match():
    want, html = _expected(), report_check.html_counts(os.path.join(_report(), "report.html"))
    assert html["counts"] == {count: want[count] for count in report_check.COUNTS}, (html, want)
    assert not html["other_statuses"], html
    assert html["card_tests"] == html["card_of"] == want["tests"] and html["card_passed"] == want["passed"], html


def html_failure_list_opens_expands_and_scrolls():
    want = _expected()
    run = report_check.browser_check(os.path.join(_report(), "report.html"), SIZE["reruns"], timeout=60, offline=True)
    assert not run["problems"], run
    assert run["counts"] == dict({count: want[count] for count in report_check.COUNTS}, rows=want["tests"]), run
    assert run["status_menu"] == {"success": want["passed"], "fail": want["failures"], "error": want["errors"],
                                  "skip": want["skipped"]}, run
    # timed, never judged here (budgets belong to the speed tasks); printed so a run shows them
    print("report timings: " + ", ".join("{} {:.2f} s".format(step, s) for step, s in run["seconds"].items()))


html_failure_list_opens_expands_and_scrolls.needs_browser = True


def browser_missing():
    """Why the browser checks can't run here, or None"""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except ImportError:
        return "Playwright is not installed (pip install playwright, see tests/stress/README.md)"
    return None


CHECKS = [xml_parses_with_a_standard_parser, xml_test_and_rerun_counts_match, xml_failure_error_skip_counts_match,
          xml_validates_against_junit_10, html_totals_match, html_failure_list_opens_expands_and_scrolls]
