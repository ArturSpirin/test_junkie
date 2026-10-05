from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.SkipSuites import SkipTests


def test_component():

    runner = Runner([SkipTests])
    aggregator = runner.run(tests=[SkipTests.test_1, SkipTests.test_2])
    metrics = aggregator.get_basic_report()["tests"]

    assert metrics[TestCategory.SUCCESS] == 2
    assert metrics[TestCategory.SKIP] == 1

    suites = runner.get_executed_suites()
    metrics = suites[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="success")
