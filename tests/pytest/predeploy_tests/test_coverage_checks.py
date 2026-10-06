import pytest

from tests.junkie_suites import coverage_checks


@pytest.mark.parametrize("check", coverage_checks.CHECKS, ids=lambda check: check.__name__)
def test_coverage_checks(check):
    check()
