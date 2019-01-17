from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener, parameters={1, 2}, retry=2)
class ErrorSuiteWrongDatatype:

    @test()
    def test_1(self, class_parameter):
        pass


@Suite(listener=TestListener)
class ErrorSuite2:

    @test(parameters=[1, 2])
    def test_1(self):
        pass


@Suite(listener=TestListener)
class ErrorSuite3:

    @test(parameters={1, 2})
    def test_1(self, parameter):
        pass


@Suite(listener=TestListener)
class ErrorSuite4:

    @test(parameters=[])
    def test_1(self, parameter):
        pass


@Suite(listener=TestListener, parameters=[])
class ErrorSuite5:

    @test()
    def test_1(self, class_parameter):
        pass
