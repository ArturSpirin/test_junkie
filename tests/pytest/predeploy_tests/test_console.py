import pytest

from tests.junkie_suites import console_checks


@pytest.mark.parametrize("check", console_checks.CHECKS, ids=lambda check: check.__name__)
def test_console(check):
    check()
