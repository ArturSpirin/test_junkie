import pytest

from tests.junkie_suites import group_rules_checks


@pytest.mark.parametrize("check", group_rules_checks.CHECKS, ids=lambda check: check.__name__)
def test_group_rules(check):
    check()
