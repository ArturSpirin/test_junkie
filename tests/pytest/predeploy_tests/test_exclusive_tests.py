import pytest

from tests.junkie_suites import exclusive_checks


@pytest.mark.parametrize("check", exclusive_checks.CHECKS, ids=lambda check: check.__name__)
def test_exclusive_tests(check):
    check()
