from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.SkipSuite import SkipSuiteAdvanced


def test_component():
    runner = Runner([SkipSuiteAdvanced])
    aggregator = runner.run()
    metrics = aggregator.get_basic_report()["tests"]
    assert metrics[TestCategory.SUCCESS] == 4
    assert metrics[TestCategory.SKIP] == 4
    suites = runner.get_executed_suites()

    metrics = suites[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="success")
