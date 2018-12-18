from test_junkie.decorators import Suite, test


class A:

    def unbound(self):
        return [1, 2, 3]

    @classmethod
    def clsmethod(cls):
        return [1, 2, 3]

    @staticmethod
    def static():
        return [1, 2, 3]

    def unbound_wrong(self):
        return 1

    @classmethod
    def classmethod_wrong(cls):
        return "derp"

    @staticmethod
    def static_wrong():
        return {1: 2}


def func():
    return [1, 2, 3]


def func_wrong():
    return True


@Suite(parameters=A().unbound)
class ParametersSuite:

    def __init__(self):

        pass

    @test(parameters=A().unbound)
    def a(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=A().static)
    def b(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=A().clsmethod)
    def c(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=func)
    def d(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=A().unbound_wrong)
    def e(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=A().static_wrong)
    def f(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=A().classmethod_wrong)
    def g(self, parameter, suite_parameter):
        print(parameter, suite_parameter)

    @test(parameters=func_wrong)
    def h(self, parameter, suite_parameter):
        print(parameter, suite_parameter)
