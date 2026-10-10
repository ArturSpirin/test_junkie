import pytest

from tests.junkie_suites import console_coverage_checks


@pytest.mark.parametrize("check", console_coverage_checks.CHECKS, ids=lambda check: check.__name__)
def test_console_coverage_checks(check):
    check()
