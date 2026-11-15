import pytest

from tests.junkie_suites import patch_checks


@pytest.mark.parametrize("check", patch_checks.CHECKS, ids=lambda check: check.__name__)
def test_patch(check):
    check()
