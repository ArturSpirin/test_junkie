from test_junkie.decorators import Suite, test, afterTest, beforeTest
from test_junkie.rules import Rules
from tests.junkie_suites.TestListener import TestListener


@Suite(listener=TestListener, parameters=[1, 2], retry=2)
class ExecutionSequence1:

    @beforeTest()
    def before_test(self):
        assert True is False

    @afterTest()
    def after_test(self):
        pass

    @test()
    def test_1(self):
        pass

    @test()
    def test_2(self):
        pass

    @test(parameters=[1, 2], retry=2)
    def test_3(self, suite_parameter, parameter):
        pass


@Suite(listener=TestListener, parameters=[1, 2], retry=2)
class ExecutionSequence2:

    @beforeTest()
    def before_test(self):
        pass

    @afterTest()
    def after_test(self):
        assert True is False

    @test()
    def test_1(self):
        pass

    @test()
    def test_2(self):
        pass

    @test(parameters=[1, 2], retry=2)
    def test_3(self, suite_parameter, parameter):
        pass


@Suite(listener=TestListener, parameters=[1, 2], retry=2)
class ExecutionSequence3:

    @beforeTest()
    def before_test(self):
        pass

    @afterTest()
    def after_test(self):
        pass

    @test()
    def test_1(self):
        assert True is False

    @test()
    def test_2(self):
        pass

    @test(parameters=[1, 2], retry=2)
    def test_3(self, suite_parameter, parameter):
        pass


@Suite(listener=TestListener, parameters=[1, 2], rules=Rules)
class ExecutionSequence4:

    @beforeTest()
    def before_test(self):
        assert True is False

    @afterTest()
    def after_test(self):
        assert True is False

    @test(skip_after_test=True, skip_before_test=True,
          skip_after_test_rule=True, skip_before_test_rule=True)
    def test_1(self):
        pass

    @test(skip_after_test=True, skip_before_test=True,
          skip_after_test_rule=True, skip_before_test_rule=True)
    def test_2(self):
        pass

    @test(parameters=[1, 2],
          skip_after_test=True, skip_before_test=True,
          skip_after_test_rule=True, skip_before_test_rule=True)
    def test_3(self, suite_parameter, parameter):
        pass
