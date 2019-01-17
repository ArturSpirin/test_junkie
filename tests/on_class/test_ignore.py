import pprint

from test_junkie.errors import BadParameters
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBoundMethod, IgnoreSuiteFunction, IgnoreSuiteClassic, \
    IgnoreSuiteClassic2, IgnoreSuiteClassic3

runner = Runner(IgnoreSuiteBoundMethod)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner = Runner(IgnoreSuiteFunction)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics2():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics2():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner = Runner(IgnoreSuiteClassic)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics3():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics3():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner = Runner(IgnoreSuiteClassic2)
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics4():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="ignore",
                                       expected_retry_count=0)


def test_test_metrics4():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0


runner = Runner(IgnoreSuiteClassic3)
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
        from tests.junkie_suites.ErrorSuite import ErrorSuiteWrongDatatype
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


def test_wrong_params2():

    try:
        from tests.junkie_suites.ErrorSuite import ErrorSuite2
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


def test_wrong_params3():

    try:
        from tests.junkie_suites.ErrorSuite import ErrorSuite3
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


def test_wrong_params4():

    try:
        from tests.junkie_suites.ErrorSuite import ErrorSuite4
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"


def test_wrong_params5():

    try:
        from tests.junkie_suites.ErrorSuite import ErrorSuite5
        raise AssertionError("This test must raise exception, as wrang datatype is used for parameters")
    except Exception as error:
        assert isinstance(error, BadParameters), "Exception must be raised for bad parameters"
