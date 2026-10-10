import pytest

from tests.junkie_suites import core_coverage_checks


@pytest.mark.parametrize("check", core_coverage_checks.CHECKS, ids=lambda check: check.__name__)
def test_core_coverage_checks(check):
    check()
