from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.BasicSuite import BasicSuite
from tests.junkie_suites.ParametersSuite import ParametersSuite

runner = Runner(BasicSuite)
runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="fail",
                                       expected_beforeclass_exception_count=1,
                                       expected_beforeclass_exception_object=None,
                                       expected_beforeclass_performance_count=1,

                                       expected_afterclass_exception_count=1,
                                       expected_afterclass_exception_object=None,
                                       expected_afterclass_performance_count=1,

                                       expected_beforetest_exception_count=8,
                                       expected_beforetest_exception_object=None,
                                       expected_beforetest_performance_count=8,

                                       expected_aftertest_exception_count=4,
                                       expected_aftertest_exception_object=None,
                                       expected_aftertest_performance_count=4)


def test_failure():

    tested = False
    for test in tests:
        if test.get_function_name() == "failure":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="fail",
                                              expected_exception=AssertionError)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_error():

    tested = False
    for test in tests:
        if test.get_function_name() == "error":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_exception=Exception)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="skip")
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip_function():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip_function":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="skip")
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="fail",
                                              expected_exception=AssertionError,
                                              expected_retry_count=2,
                                              expected_performance_count=2,
                                              expected_exception_count=2)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_parameters():

    tested = False
    for test in tests:
        if test.get_function_name() == "parameters":
            properties = test.metrics.get_metrics()["None"]
            for param, metrics in properties.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param)
            tested = True
    if not tested:
        raise Exception("Test did not run")


def test_parameters_plus_plus():
    runner = Runner([ParametersSuite])
    aggregator = runner.run()
    metrics = aggregator.get_basic_report()["tests"]
    assert metrics[TestCategory.SUCCESS] == 36
    assert metrics[TestCategory.IGNORE] == 4
    suites = runner.get_executed_suites()
    metrics = suites[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="fail")
