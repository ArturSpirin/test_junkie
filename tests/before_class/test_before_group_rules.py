import pprint

from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBeforeGroupRule, IgnoreSuiteBeforeGroupRule2

runner = Runner([IgnoreSuiteBeforeGroupRule, IgnoreSuiteBeforeGroupRule2])
runner.run()

results = runner.get_executed_suites()
tests = results[0].get_test_objects()
pprint.pprint(results[0].metrics.get_metrics())
for test in tests:
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_before_group_exceptions():

    for suite in results:
        metrics = suite.metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="ignore",
                                           expected_retry_count=0)
