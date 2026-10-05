import pprint
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.AfterClassExceptionSuite import AfterClassExceptionSuite

runner = Runner([AfterClassExceptionSuite])
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_beforeclass_exception_count=1,
                                       expected_beforeclass_exception_object=None,
                                       expected_beforeclass_performance_count=1,

                                       expected_afterclass_exception_count=1,
                                       expected_afterclass_exception_object=Exception,
                                       expected_afterclass_performance_count=1)


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics)
