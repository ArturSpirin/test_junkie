import pprint

from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AfterTestAssertionSuite import AfterTestAssertionSuite
from tests.junkie_suites.AfterTestExceptionSuite import AfterTestExceptionSuite
from tests.junkie_suites.BeforeTestAssertionSuite import BeforeTestAssertionSuite
from tests.junkie_suites.BeforeTestExceptionSuite import BeforeTestExceptionSuite

runner = Runner([BeforeTestAssertionSuite])
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


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


runner2 = Runner([BeforeTestExceptionSuite])
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


runner3 = Runner([AfterTestAssertionSuite])
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
        pprint.pprint(metrics)
        QualityManager.check_test_metrics(metrics,
                                          expected_status="fail",
                                          expected_retry_count=4,
                                          expected_exception_count=4,
                                          expected_performance_count=4,
                                          expected_exception=AssertionError)


runner4 = Runner([AfterTestExceptionSuite])
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
