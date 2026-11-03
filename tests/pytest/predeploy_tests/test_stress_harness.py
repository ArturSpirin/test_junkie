import pytest

from tests.junkie_suites import stress_checks


@pytest.mark.parametrize("check", stress_checks.CHECKS, ids=lambda check: check.__name__)
def test_stress_harness(check):
    check()
