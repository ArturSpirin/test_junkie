import pprint

from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.SkipSuite import SkipSuite

runner = Runner([SkipSuite])
runner.run()
results = runner.get_executed_suites()

pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics,
                                       expected_status="skip",
                                       expected_retry_count=0)


def test_test_metrics():

    assert results[0].get_test_objects()
    for test in results[0].get_test_objects():

        properties = test.metrics.get_metrics()
        assert len(properties) == 0
