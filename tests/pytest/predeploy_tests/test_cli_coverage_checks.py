import pytest

from tests.junkie_suites import cli_coverage_checks


@pytest.mark.parametrize("check", cli_coverage_checks.CHECKS, ids=lambda check: check.__name__)
def test_cli_coverage_checks(check):
    check()
