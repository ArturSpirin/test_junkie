import pprint

from test_junkie.debugger import LogJunkie
from tests.QualityManager import QualityManager

LogJunkie.enable_logging(10)
from test_junkie.runner import Runner
from tests.junkie_suites.Retry import Retries

runner = Runner([Retries])
runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()
pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="fail",
                                       expected_retry_count=3)


def test_retry_on_exception():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry_on_exception":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_retry_count=9,
                                              expected_performance_count=9,
                                              expected_exception_count=9,
                                              expected_status="error",
                                              expected_exception=Exception)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry_on_assertion():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry_on_assertion":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_retry_count=9,
                                              expected_performance_count=9,
                                              expected_exception_count=9,
                                              expected_status="fail",
                                              expected_exception=AssertionError)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry_on_exception():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry_on_exception":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_exception=Exception)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry_on_assertion():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry_on_assertion":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="fail",
                                              expected_exception=AssertionError)
            tested = True
    if not tested:
        raise Exception("Test did not run")
