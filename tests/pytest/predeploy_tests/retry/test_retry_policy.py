import pytest

from tests.junkie_suites import retry_policy_checks


@pytest.mark.parametrize("check", retry_policy_checks.CHECKS, ids=lambda check: check.__name__)
def test_retry_policy(check):
    check()
