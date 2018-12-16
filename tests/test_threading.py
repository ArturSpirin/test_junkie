import pprint
import sys
sys.path.insert(1, __file__.split("tests")[0])
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.ParallelSuiteA import ParallelSuiteA
from tests.junkie_suites.ParallelSuiteB import ParallelSuiteB
from tests.junkie_suites.ParallelSuiteC import ParallelSuiteC

runner = Runner([ParallelSuiteA, ParallelSuiteB, ParallelSuiteC])
runner.run(test_multithreading_limit=2, suite_multithreading_limit=2)
results = runner.get_executed_suites()

for suite_object in results:
    print(suite_object.get_class_name())
    pprint.pprint(suite_object.metrics.get_metrics())


def test_class_metrics():

    assert results[0].get_class_name() == "ParallelSuiteA"
    metrics = results[0].metrics.get_metrics()
    assert int(metrics["runtime"]) < int(results[1].metrics.get_metrics()["runtime"])
    assert int(metrics["runtime"]) < int(results[2].metrics.get_metrics()["runtime"])
    QualityManager.check_class_metrics(metrics,
                                       expected_status="success",
                                       expected_retry_count=1)


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])


def test_class_metrics2():

    assert results[1].get_class_name() == "ParallelSuiteB"
    metrics = results[1].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="success",
                                       expected_retry_count=1)


def test_test_metrics2():

    assert results[1].get_test_objects()
    for test in results[1].get_test_objects():
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])


def test_class_metrics3():

    assert results[2].get_class_name() == "ParallelSuiteC"
    metrics = results[2].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="success",
                                       expected_retry_count=1)


def test_test_metrics3():

    assert results[2].get_test_objects()
    for test in results[2].get_test_objects():
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])
