import pytest

from tests.junkie_suites import listener_error_checks


@pytest.mark.parametrize("check", listener_error_checks.CHECKS, ids=lambda check: check.__name__)
def test_listener_errors(check):
    check()
