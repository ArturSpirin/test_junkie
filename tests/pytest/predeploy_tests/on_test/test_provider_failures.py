import pytest

from tests.junkie_suites import provider_checks


@pytest.mark.parametrize("check", provider_checks.CHECKS, ids=lambda check: check.__name__)
def test_provider_failures(check):
    check()
