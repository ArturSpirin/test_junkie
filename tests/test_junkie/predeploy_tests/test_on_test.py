from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AfterTestAssertionSuite import AfterTestAssertionSuite
from tests.junkie_suites.AfterTestExceptionSuite import AfterTestExceptionSuite
from tests.junkie_suites.BeforeTestAssertionSuite import BeforeTestAssertionSuite
from tests.junkie_suites.BeforeTestExceptionSuite import BeforeTestExceptionSuite


@Suite()
class BeforeTestAssertionSuiteTests:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([BeforeTestAssertionSuite])
        runner.run()
        BeforeTestAssertionSuiteTests._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = BeforeTestAssertionSuiteTests._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_retry_count=2,
                                           expected_status="fail",
                                           expected_beforetest_exception_count=8,
                                           expected_beforetest_exception_object=AssertionError,
                                           expected_beforetest_performance_count=8)

    @test()
    def test_metrics(self):
        for t in BeforeTestAssertionSuiteTests._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="fail",
                                              expected_retry_count=4,
                                              expected_exception_count=4,
                                              expected_performance_count=4,
                                              expected_exception=AssertionError)


@Suite()
class BeforeTestExceptionSuiteTests:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([BeforeTestExceptionSuite])
        runner.run()
        BeforeTestExceptionSuiteTests._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = BeforeTestExceptionSuiteTests._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_retry_count=2,
                                           expected_status="fail",
                                           expected_beforetest_exception_count=8,
                                           expected_beforetest_exception_object=Exception,
                                           expected_beforetest_performance_count=8)

    @test()
    def test_metrics(self):
        for t in BeforeTestExceptionSuiteTests._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_retry_count=4,
                                              expected_exception_count=4,
                                              expected_performance_count=4,
                                              expected_exception=Exception)


@Suite()
class AfterTestAssertionSuiteTests:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([AfterTestAssertionSuite])
        runner.run()
        AfterTestAssertionSuiteTests._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = AfterTestAssertionSuiteTests._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_retry_count=2,
                                           expected_status="fail",
                                           expected_aftertest_exception_count=8,
                                           expected_aftertest_exception_object=AssertionError,
                                           expected_aftertest_performance_count=8)

    @test()
    def test_metrics(self):
        for t in AfterTestAssertionSuiteTests._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="fail",
                                              expected_retry_count=4,
                                              expected_exception_count=4,
                                              expected_performance_count=4,
                                              expected_exception=AssertionError)


@Suite()
class AfterTestExceptionSuiteTests:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([AfterTestExceptionSuite])
        runner.run()
        AfterTestExceptionSuiteTests._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = AfterTestExceptionSuiteTests._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_retry_count=2,
                                           expected_status="fail",
                                           expected_aftertest_exception_count=8,
                                           expected_aftertest_exception_object=Exception,
                                           expected_aftertest_performance_count=8)

    @test()
    def test_metrics(self):
        for t in AfterTestExceptionSuiteTests._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_retry_count=4,
                                              expected_exception_count=4,
                                              expected_performance_count=4,
                                              expected_exception=Exception)
