from test_junkie.decorators import Suite, test
from tests.junkie_suites import capture_output_checks


@Suite()
class CaptureOutputSuite:

    @test(parameters=capture_output_checks.CHECKS)
    def capture_output(self, parameter):
        parameter()
