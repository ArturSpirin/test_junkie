from test_junkie.decorators import Suite, test
from tests.junkie_suites.TestListener import TestListener


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


@Suite(listener=TestListener, parameters={1, 2}, retry=2)
class IgnoreSuiteWrongDatatype:

    @test()
    def pass_1(self):
        pass
