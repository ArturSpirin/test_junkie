from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.BeforeClassAssertionSuite import BeforeClassAssertionSuite

runner = Runner([BeforeClassAssertionSuite])
runner.run()
results = runner.get_executed_suites()


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="fail",
                                       expected_retry_count=2,
                                       expected_beforeclass_exception_count=2,
                                       expected_beforeclass_exception_object=AssertionError,
                                       expected_beforeclass_performance_count=2)


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics,
                                          expected_status="ignore",
                                          expected_exception_count=2,
                                          expected_performance_count=2,
                                          expected_retry_count=2,
                                          expected_exception=AssertionError)
