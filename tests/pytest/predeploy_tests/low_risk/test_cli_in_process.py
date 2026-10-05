import pytest

from tests.junkie_suites import cli_checks


@pytest.mark.parametrize("check", cli_checks.CHECKS, ids=lambda check: check.__name__)
def test_cli(check):
    check()
