import pprint

from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AfterTestSuite import AfterTestSuite1, AfterTestSuite2
from tests.junkie_suites.BeforeTestSuite import BeforeTestSuite1, BeforeTestSuite2

runner = Runner(BeforeTestSuite1)
runner.run()
results = runner.get_executed_suites()


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    pprint.pprint(metrics)
    QualityManager.check_class_metrics(metrics,
                                       expected_retry_count=2,
                                       expected_status="fail",
                                       expected_beforetest_exception_count=8,
                                       expected_beforetest_exception_object=AssertionError,
                                       expected_beforetest_performance_count=8)


def test_failure():
    tests = results[0].get_test_objects()
    for test in tests:
        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics,
                                          expected_status="fail",
                                          expected_retry_count=4,
                                          expected_exception_count=4,
                                          expected_performance_count=4,
                                          expected_exception=AssertionError)


runner2 = Runner(BeforeTestSuite2)
runner2.run()
results2 = runner2.get_executed_suites()


def test_class_metrics2():

    metrics = results2[0].metrics.get_metrics()
    pprint.pprint(metrics)
    QualityManager.check_class_metrics(metrics,
                                       expected_retry_count=2,
                                       expected_status="fail",
                                       expected_beforetest_exception_count=8,
                                       expected_beforetest_exception_object=Exception,
                                       expected_beforetest_performance_count=8)


def test_failure2():
    tests = results2[0].get_test_objects()
    for test in tests:
        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics,
                                          expected_status="error",
                                          expected_retry_count=4,
                                          expected_exception_count=4,
                                          expected_performance_count=4,
                                          expected_exception=Exception)


runner3 = Runner(AfterTestSuite1)
runner3.run()
results3 = runner3.get_executed_suites()


def test_class_metrics3():

    metrics = results3[0].metrics.get_metrics()
    pprint.pprint(metrics)
    QualityManager.check_class_metrics(metrics,
                                       expected_retry_count=2,
                                       expected_status="fail",
                                       expected_aftertest_exception_count=8,
                                       expected_aftertest_exception_object=AssertionError,
                                       expected_aftertest_performance_count=8)


def test_failure3():
    tests = results3[0].get_test_objects()
    for test in tests:
        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics,
                                          expected_status="fail",
                                          expected_retry_count=4,
                                          expected_exception_count=4,
                                          expected_performance_count=4,
                                          expected_exception=AssertionError)


runner4 = Runner(AfterTestSuite2)
runner4.run()
results4 = runner4.get_executed_suites()


def test_class_metrics4():

    metrics = results4[0].metrics.get_metrics()
    pprint.pprint(metrics)
    QualityManager.check_class_metrics(metrics,
                                       expected_retry_count=2,
                                       expected_status="fail",
                                       expected_aftertest_exception_count=8,
                                       expected_aftertest_exception_object=Exception,
                                       expected_aftertest_performance_count=8)


def test_failure4():
    tests = results4[0].get_test_objects()
    for test in tests:
        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics,
                                          expected_status="error",
                                          expected_retry_count=4,
                                          expected_exception_count=4,
                                          expected_performance_count=4,
                                          expected_exception=Exception)
