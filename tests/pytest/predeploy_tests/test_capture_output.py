import pytest

from tests.junkie_suites import capture_output_checks


@pytest.mark.parametrize("check", capture_output_checks.CHECKS, ids=lambda check: check.__name__)
def test_capture_output(check):
    check()
