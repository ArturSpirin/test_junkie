import pytest

from tests.junkie_suites import param_key_checks


@pytest.mark.parametrize("check", param_key_checks.CHECKS, ids=lambda check: check.__name__)
def test_param_keys(check):
    check()
