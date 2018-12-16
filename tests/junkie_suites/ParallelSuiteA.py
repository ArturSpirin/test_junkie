import time

from test_junkie.decorators import Suite, test
from tests.junkie_suites.ParallelSuiteB import ParallelSuiteB
from tests.junkie_suites.ParallelSuiteC import ParallelSuiteC


@Suite(pr=[ParallelSuiteC])
class ParallelSuiteA:

    @test(priority=1, parameters=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], parallelized_parameters=True, pr=[ParallelSuiteB.a])
    def a(self, parameter):
        time.sleep(1)

    @test(priority=3, parameters=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], pr=[ParallelSuiteB.a])
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

    @test(priority=1, pr=[ParallelSuiteB.i])
    def i(self):
        time.sleep(1)

    @test(priority=1)
    def j(self):
        pass

    @test(priority=2, pr=[ParallelSuiteB.k])
    def k(self):
        time.sleep(1)
