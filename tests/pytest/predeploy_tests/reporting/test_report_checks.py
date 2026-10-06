import pytest

from tests.junkie_suites import report_checks


@pytest.mark.parametrize("check", report_checks.CHECKS, ids=lambda check: check.__name__)
def test_report(check):
    check()
