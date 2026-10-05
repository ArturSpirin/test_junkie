from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.Retry import Retries


@Suite()
class RetryTestSuite:

    _results = None
    _tests = None

    @beforeClass()
    def setup(self):
        runner = Runner([Retries])
        runner.run()
        RetryTestSuite._results = runner.get_executed_suites()
        RetryTestSuite._tests = RetryTestSuite._results[0].get_test_objects()

    @test()
    def class_metrics(self):
        metrics = RetryTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics, expected_status="fail", expected_retry_count=3)

    @test()
    def retry_on_exception(self):
        found = next((t for t in RetryTestSuite._tests
                      if t.get_function_name() == "retry_on_exception"), None)
        assert found is not None
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_retry_count=9, expected_performance_count=9,
                                          expected_exception_count=9, expected_status="error",
                                          expected_exception=Exception)

    @test()
    def retry_on_assertion(self):
        found = next((t for t in RetryTestSuite._tests
                      if t.get_function_name() == "retry_on_assertion"), None)
        assert found is not None
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_retry_count=9, expected_performance_count=9,
                                          expected_exception_count=9, expected_status="fail",
                                          expected_exception=AssertionError)

    @test()
    def no_retry_on_exception(self):
        found = next((t for t in RetryTestSuite._tests
                      if t.get_function_name() == "no_retry_on_exception"), None)
        assert found is not None
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="error", expected_exception=Exception)

    @test()
    def no_retry_on_assertion(self):
        found = next((t for t in RetryTestSuite._tests
                      if t.get_function_name() == "no_retry_on_assertion"), None)
        assert found is not None
        metrics = found.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics, expected_status="fail", expected_exception=AssertionError)

    @test()
    def suite_actual_retry_count(self):
        assert RetryTestSuite._results[0].get_number_of_actual_retries() == 3

