import pytest

from tests.junkie_suites import conflict_checks


@pytest.mark.parametrize("check", conflict_checks.CHECKS, ids=lambda check: check.__name__)
def test_conflicts(check):
    check()
