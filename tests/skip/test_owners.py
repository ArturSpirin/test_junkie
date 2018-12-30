from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.SkipSuites import SkipOwner


def test_component():

    runner = Runner([SkipOwner])
    aggregator = runner.run(owners=["Jane Doe"])
    metrics = aggregator.get_basic_report()["tests"]

    assert metrics[TestCategory.SUCCESS] == 1
    assert metrics[TestCategory.SKIP] == 2

    suites = runner.get_executed_suites()
    metrics = suites[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="success")
