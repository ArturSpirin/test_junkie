from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener, parameters={1, 2}, retry=2)
class ErrorSuiteWrongDatatype:

    @test()
    def pass_1(self, class_parameter):
        pass
