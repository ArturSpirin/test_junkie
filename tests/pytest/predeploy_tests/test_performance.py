import pytest

from tests.junkie_suites import perf_checks


@pytest.mark.parametrize("check", perf_checks.CHECKS, ids=lambda check: check.__name__)
def test_performance(check):
    check()
