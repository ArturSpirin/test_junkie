import pytest

from tests.junkie_suites.skip import CombinedFilterSuites as fixture


@pytest.mark.parametrize("filters, expected", fixture.CASES)
def test_filters_combine_with_and(filters, expected):
    assert fixture.run(**filters) == sorted(expected)
