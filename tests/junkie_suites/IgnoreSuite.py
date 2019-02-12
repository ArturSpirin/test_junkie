from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener
from tests.junkie_suites.TestRules import TestRules


class Bound:

    def __init__(self):

        pass

    def get_params(self):

        return []


def get_params():
    return []


@Suite(listener=TestListener, parameters=Bound().get_params, retry=2)
class IgnoreSuiteBoundMethod:

    @test()
    def pass_1(self):
        pass


@Suite(listener=TestListener, parameters=get_params, retry=3)
class IgnoreSuiteFunction:

    @test()
    def pass_1(self):
        pass


@Suite(listener=TestListener, parameters=[], retry=2)
class IgnoreSuiteClassic:

    @test()
    def pass_1(self):
        pass


@Suite(listener=TestListener, parameters=get_params(), retry=2)
class IgnoreSuiteClassic2:

    @test()
    def pass_1(self):
        pass


@Suite(listener=TestListener, parameters=Bound().get_params(), retry=2)
class IgnoreSuiteClassic3:

    @test()
    def pass_1(self):
        pass


@Suite(listener=TestListener, retry=2, rules=TestRules)
class IgnoreSuiteBeforeGroupRule:

    @test()
    def ignore_1(self):
        pass

    @test()
    def ignore_2(self):
        pass


@Suite(listener=TestListener, retry=2, rules=TestRules)
class IgnoreSuiteBeforeGroupRule2:

    @test()
    def ignore_1(self):
        pass

    @test()
    def ignore_2(self):
        pass
