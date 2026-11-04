import pytest

from tests.junkie_suites import stress_checks


@pytest.mark.parametrize("check", stress_checks.CHECKS, ids=lambda check: check.__name__)
def test_stress_harness(check):
    check()


@pytest.mark.skipif(not stress_checks.LARGE_ENABLED, reason="large stress sizes run on demand: set TJ_STRESS_LARGE=1")
@pytest.mark.parametrize("check", stress_checks.LARGE_CHECKS, ids=lambda check: check.__name__)
def test_stress_budget_large(check):
    check()
