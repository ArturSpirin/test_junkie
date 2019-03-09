import pprint

from test_junkie.errors import BadParameters, BadSignature
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBoundMethod, IgnoreSuiteFunction, IgnoreSuiteClassic, \
    IgnoreSuiteClassic2, IgnoreSuiteClassic3
from tests.junkie_suites.error_handling.ErrorSuite4 import ErrorSuite4
from tests.junkie_suites.error_handling.ErrorSuite5 import ErrorSuite5

runner1 = Runner([IgnoreSuiteBoundMethod])
runner1.run()
results1 = runner1.get_executed_suites()

pprint.pprint(results1[0].metrics.get_metrics())
for test in results1[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results1[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics():

    assert results1[0].get_test_objects()
    for test in results1[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner2 = Runner([IgnoreSuiteFunction])
runner2.run()
results2 = runner2.get_executed_suites()

pprint.pprint(results2[0].metrics.get_metrics())
for test in results2[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics2():

    metrics = results2[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics2():

    assert results2[0].get_test_objects()
    for test in results2[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner3 = Runner([IgnoreSuiteClassic])
runner3.run()
results3 = runner3.get_executed_suites()

pprint.pprint(results3[0].metrics.get_metrics())
for test in results3[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics3():

    metrics = results3[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics3():

    assert results3[0].get_test_objects()
    for test in results3[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner4 = Runner([IgnoreSuiteClassic2])
runner4.run()
results4 = runner4.get_executed_suites()

pprint.pprint(results4[0].metrics.get_metrics())
for test in results4[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics4():

    metrics = results4[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics4():

    assert results4[0].get_test_objects()
    for test in results4[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner = Runner([IgnoreSuiteClassic3])
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics5():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics5():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


def test_wrong_params():

    try:
        from tests.junkie_suites.error_handling import ErrorSuite1
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


def test_wrong_params2():

    try:
        from tests.junkie_suites.error_handling import ErrorSuite2
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadSignature), "Exception must be raised for bad signature"


def test_wrong_params3():

    try:
        from tests.junkie_suites.error_handling.ErrorSuite3 import ErrorSuite3
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


runner5 = Runner([ErrorSuite4])
runner5.run()
results5 = runner5.get_executed_suites()

pprint.pprint(results5[0].metrics.get_metrics())
for test in results5[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_before_test_error1():

    metrics5 = results5[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics5,
                                       expected_status="fail",
                                       expected_retry_count=1,
                                       expected_beforetest_exception_count=1,
                                       expected_beforetest_exception_object=Exception,
                                       expected_beforetest_performance_count=1)


def test_before_test_error2():

    assert results5[0].get_test_objects()
    for test in results5[0].get_test_objects():

        if test.get_function_name() == "failure":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_exception=Exception)


runner6 = Runner([ErrorSuite5])
runner6.run()
results6 = runner6.get_executed_suites()

pprint.pprint(results6[0].metrics.get_metrics())
for test in results6[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_after_test_error3():

    metrics6 = results6[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics6,
                                       expected_status="fail",
                                       expected_retry_count=1,
                                       expected_aftertest_exception_count=1,
                                       expected_aftertest_exception_object=Exception,
                                       expected_aftertest_performance_count=1)


def test_after_test_error4():

    assert results6[0].get_test_objects()
    for test in results6[0].get_test_objects():

        if test.get_function_name() == "failure":
            metrics = test.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics,
                                              expected_status="error",
                                              expected_exception=Exception)
