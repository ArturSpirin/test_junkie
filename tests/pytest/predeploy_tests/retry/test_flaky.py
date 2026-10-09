import pytest

from tests.junkie_suites import flaky_checks


@pytest.mark.parametrize("check", flaky_checks.CHECKS, ids=lambda check: check.__name__)
def test_flaky(check):
    check()
