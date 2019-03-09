import time

from test_junkie.decorators import Suite, test
from tests.junkie_suites.ParallelSuiteC import ParallelSuiteC


@Suite()
class ParallelSuiteB:

    @test(priority=1, parameters=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], pr=[ParallelSuiteC.a])
    def a(self, parameter):
        time.sleep(1)

    @test(priority=3, parameters=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    def b(self, parameter):
        time.sleep(1)

    @test(priority=1)
    def c(self):
        time.sleep(1)

    @test(priority=2)
    def d(self):
        pass

    @test(priority=2)
    def e(self):
        time.sleep(1)

    @test(priority=1)
    def f(self):
        pass

    @test(priority=1)
    def g(self):
        time.sleep(1)

    @test(priority=1)
    def h(self):
        pass

    @test(priority=1)
    def i(self):
        time.sleep(1)

    @test(priority=1)
    def j(self):
        pass

    @test(priority=2)
    def k(self):
        time.sleep(1)
