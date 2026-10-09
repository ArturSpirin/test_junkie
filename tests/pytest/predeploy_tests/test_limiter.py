import pytest

from tests.junkie_suites import limiter_checks


@pytest.mark.parametrize("check", limiter_checks.CHECKS, ids=lambda check: check.__name__)
def test_limiter(check):
    check()
