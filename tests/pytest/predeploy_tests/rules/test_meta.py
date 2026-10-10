import pytest

from tests.junkie_suites import meta_checks


@pytest.mark.parametrize("check", meta_checks.CHECKS, ids=lambda check: check.__name__)
def test_meta(check):
    check()
