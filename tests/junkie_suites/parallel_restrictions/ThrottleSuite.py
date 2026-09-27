from test_junkie.decorators import Suite, test
from tests.junkie_suites.parallel_restrictions import timeline


@Suite()
class ThrottleSuite:

    @test(parameters=[1, 2, 3], parallelized_parameters=True)
    def a(self, parameter):
        timeline.record("throttle")
