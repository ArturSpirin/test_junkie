from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AfterClassAssertionSuite import AfterClassAssertionSuite
from tests.junkie_suites.AfterClassExceptionSuite import AfterClassExceptionSuite
from tests.junkie_suites.BeforeClassAssertionSuite import BeforeClassAssertionSuite
from tests.junkie_suites.BeforeClassExceptionSuite import BeforeClassExceptionSuite
from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBeforeGroupRule, IgnoreSuiteBeforeGroupRule2


@Suite()
class BeforeGroupRulesTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([IgnoreSuiteBeforeGroupRule, IgnoreSuiteBeforeGroupRule2])
        runner.run()
        BeforeGroupRulesTestSuite._results = runner.get_executed_suites()

    @test()
    def before_group_exceptions(self):
        for suite in BeforeGroupRulesTestSuite._results:
            metrics = suite.metrics.get_metrics()
            QualityManager.check_class_metrics(metrics, expected_status="ignore", expected_retry_count=0)


@Suite()
class BeforeClassAssertionTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([BeforeClassAssertionSuite])
        runner.run()
        BeforeClassAssertionTestSuite._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = BeforeClassAssertionTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="fail",
                                           expected_retry_count=2,
                                           expected_beforeclass_exception_count=2,
                                           expected_beforeclass_exception_object=AssertionError,
                                           expected_beforeclass_performance_count=2)

    @test()
    def test_metrics(self):
        assert BeforeClassAssertionTestSuite._results[0].get_test_objects()
        for t in BeforeClassAssertionTestSuite._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="ignore",
                                              expected_exception_count=2,
                                              expected_performance_count=2,
                                              expected_retry_count=2,
                                              expected_exception=AssertionError)


@Suite()
class BeforeClassExceptionTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([BeforeClassExceptionSuite])
        runner.run()
        BeforeClassExceptionTestSuite._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = BeforeClassExceptionTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="fail",
                                           expected_retry_count=2,
                                           expected_beforeclass_exception_count=2,
                                           expected_beforeclass_exception_object=Exception,
                                           expected_beforeclass_performance_count=2)

    @test()
    def test_metrics(self):
        assert BeforeClassExceptionTestSuite._results[0].get_test_objects()
        for t in BeforeClassExceptionTestSuite._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="ignore",
                                              expected_exception_count=2,
                                              expected_performance_count=2,
                                              expected_retry_count=2,
                                              expected_exception=Exception)


@Suite()
class AfterClassAssertionTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([AfterClassAssertionSuite])
        runner.run()
        AfterClassAssertionTestSuite._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = AfterClassAssertionTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_beforeclass_exception_count=1,
                                           expected_beforeclass_exception_object=None,
                                           expected_beforeclass_performance_count=1,
                                           expected_afterclass_exception_count=1,
                                           expected_afterclass_exception_object=Exception,
                                           expected_afterclass_performance_count=1)

    @test()
    def test_metrics(self):
        assert AfterClassAssertionTestSuite._results[0].get_test_objects()
        for t in AfterClassAssertionTestSuite._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics)


@Suite()
class AfterClassExceptionTestSuite:

    _results = None

    @beforeClass()
    def setup(self):
        runner = Runner([AfterClassExceptionSuite])
        runner.run()
        AfterClassExceptionTestSuite._results = runner.get_executed_suites()

    @test()
    def class_metrics(self):
        metrics = AfterClassExceptionTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_beforeclass_exception_count=1,
                                           expected_beforeclass_exception_object=None,
                                           expected_beforeclass_performance_count=1,
                                           expected_afterclass_exception_count=1,
                                           expected_afterclass_exception_object=Exception,
                                           expected_afterclass_performance_count=1)

    @test()
    def test_metrics(self):
        assert AfterClassExceptionTestSuite._results[0].get_test_objects()
        for t in AfterClassExceptionTestSuite._results[0].get_test_objects():
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics)
