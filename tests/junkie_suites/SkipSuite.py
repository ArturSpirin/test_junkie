from test_junkie.decorators import Suite, beforeClass, afterClass, test


@Suite(skip=True)
class SkipSuite:

    @beforeClass()
    def before_class(self):
        raise Exception("Exception in before class")

    @afterClass()
    def after_class(self):
        raise Exception("Exception in after class")

    @test()
    def pass_1(self):
        pass

    @test()
    def pass_2(self):
        pass



class A:

    def do_skip(self):

        return True

    @classmethod
    def do_skip_classmethod(cls):
        return True

    @staticmethod
    def do_skip_static():
        return True

    def dont_skip(self):
        return False

    @classmethod
    def dont_skip_classmethod(cls):
        return False

    @staticmethod
    def dont_skip_static():
        return False


def do_skip():

    return True


def dont_skip():
    return False


@Suite(skip=A().dont_skip)
class SkipSuiteAdvanced:

    @test(skip=do_skip)
    def a(self):
        pass

    @test(skip=dont_skip)
    def b(self):
        pass

    @test(skip=A().do_skip)
    def c(self):
        pass

    @test(skip=A().dont_skip)
    def d(self):
        pass

    @test(skip=A().do_skip_static)
    def e(self):
        pass

    @test(skip=A().dont_skip_static)
    def f(self):
        pass

    @test(skip=A().do_skip_classmethod)
    def g(self):
        pass

    @test(skip=A().dont_skip_classmethod)
    def h(self):
        pass
