import pytest

from tests.junkie_suites import report_correctness_checks


def _param(check):
    marks = []
    if getattr(check, "known_bug", None):
        # raises: only the bug's failed assertion counts as the expected failure, not a crash (a missing xmlschema)
        marks.append(pytest.mark.xfail(strict=True, raises=AssertionError, reason=check.known_bug))
    return pytest.param(check, marks=marks, id=check.__name__)


@pytest.mark.parametrize("check", [_param(check) for check in report_correctness_checks.CHECKS])
def test_report_correctness(check):
    if getattr(check, "needs_browser", False):
        pytest.importorskip("playwright.sync_api", reason=report_correctness_checks.browser_missing())
    check()
