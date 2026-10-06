from test_junkie.decorators import Suite, test
from tests.junkie_suites.skip import CombinedFilterSuites as fixture


@Suite()
class CombinedFiltersTestSuite:

    @test(parameters=fixture.CASES)
    def filters_combine_with_and(self, parameter):
        filters, expected = parameter
        assert fixture.run(**filters) == sorted(expected)
