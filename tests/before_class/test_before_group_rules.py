from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.IgnoreSuite import IgnoreSuiteBeforeGroupRule

runner = Runner([IgnoreSuiteBeforeGroupRule])
runner.run()
results = runner.get_executed_suites()


def test_class_metrics4():

    for suite in results:
        metrics = suite.metrics.get_metrics()
        QualityManager.check_class_metrics(metrics,
                                           expected_status="ignore",
                                           expected_retry_count=0)
