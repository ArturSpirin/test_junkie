import pytest

from tests.junkie_suites import core_checks


@pytest.mark.parametrize("check", core_checks.CHECKS, ids=lambda check: check.__name__)
def test_core(check):
    check()
