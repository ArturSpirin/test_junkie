import pytest

from tests.junkie_suites import run_error_checks


@pytest.mark.parametrize("check", run_error_checks.CHECKS, ids=lambda check: check.__name__)
def test_run_errors(check):
    check()
