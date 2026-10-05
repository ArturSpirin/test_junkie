import pprint
import sys


sys.path.insert(1, __file__.split("tests")[0])
from tests.QualityManager import QualityManager
from test_junkie.debugger import LogJunkie
LogJunkie.enable_logging(10)

from test_junkie.runner import Runner
from tests.junkie_suites.AdvancedSuite import AdvancedSuite

runner = Runner([AdvancedSuite])
runner.run(suite_multithreading=True, suite_multithreading_limit=5,
           test_multithreading=True, test_multithreading_limit=5,
           tag_config={"run_on_match_all": ["critical", "v2"],
                       "run_on_match_any": ["critical2"],
                       "skip_on_match_all": ["skip", "v2"],
                       "skip_on_match_any": ["trivial"]})
results = runner.get_executed_suites()
tests = results[0].get_test_objects()

pprint.pprint(results[0].metrics.get_metrics())
for test in tests:
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_stats():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="fail",
                                       expected_retry_count=2,

                                       expected_beforeclass_exception_count=4,
                                       expected_beforeclass_exception_object=None,
                                       expected_beforeclass_performance_count=4,

                                       expected_afterclass_exception_count=4,
                                       expected_afterclass_exception_object=None,
                                       expected_afterclass_performance_count=4,

                                       expected_beforetest_exception_count=29,
                                       expected_beforetest_exception_object=None,
                                       expected_beforetest_performance_count=29,

                                       expected_aftertest_exception_count=29,
                                       expected_aftertest_exception_object=None,
                                       expected_aftertest_performance_count=29)


def test_no_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry2():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry2":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_no_retry3():

    tested = False
    for test in tests:
        if test.get_function_name() == "no_retry3":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="success",
                                                      expected_param=param,
                                                      expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="fail",
                                                      expected_exception=AssertionError,
                                                      expected_retry_count=4,
                                                      expected_exception_count=4,
                                                      expected_performance_count=4,
                                                      expected_class_param=metrics["class_param"])
                    for i in metrics["exceptions"]:
                        assert str(i.with_traceback(None)) == "Expected Assertion Error"
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry2():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry2":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="skip",
                                                      expected_retry_count=2,
                                                      expected_exception_count=2,
                                                      expected_performance_count=2)
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry3():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry3":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    if metrics["param"] == 10 and metrics["class_param"] == 1:

                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="error",
                                                          expected_exception=Exception,
                                                          expected_retry_count=4,
                                                          expected_exception_count=4,
                                                          expected_performance_count=4,
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                        for i in metrics["exceptions"]:
                            assert str(i.with_traceback(None)) == "On purpose"
                    else:
                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="success",
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry4():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry4":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    if metrics["param"] == 10:

                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="error",
                                                          expected_exception=Exception,
                                                          expected_retry_count=4,
                                                          expected_exception_count=4,
                                                          expected_performance_count=4,
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                        for i in metrics["exceptions"]:
                            assert str(i.with_traceback(None)) == "On purpose"
                    else:
                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="success",
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_retry5():

    tested = False
    for test in tests:
        if test.get_function_name() == "retry5":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    if metrics["class_param"] == 1:
                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="error",
                                                          expected_exception=Exception,
                                                          expected_retry_count=4,
                                                          expected_exception_count=4,
                                                          expected_performance_count=4,
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                        for i in metrics["exceptions"]:
                            assert str(i.with_traceback(None)) == "On purpose"
                    else:
                        QualityManager.check_test_metrics(metrics,
                                                          expected_status="success",
                                                          expected_param=param,
                                                          expected_class_param=metrics["class_param"])
                    tested = True
    if not tested:
        raise Exception("Test did not run")


def test_skip():

    tested = False
    for test in tests:
        if test.get_function_name() == "skip":
            for class_param, class_data in test.metrics.get_metrics().items():
                for param, metrics in class_data.items():
                    QualityManager.check_test_metrics(metrics,
                                                      expected_status="skip",
                                                      expected_retry_count=2,
                                                      expected_exception_count=2,
                                                      expected_performance_count=2)
                    tested = True
    if not tested:
        raise Exception("Test did not run")
