import pytest

from tests.junkie_suites import runner_coverage_checks


@pytest.mark.parametrize("check", runner_coverage_checks.CHECKS, ids=lambda check: check.__name__)
def test_runner_coverage_checks(check):
    check()
