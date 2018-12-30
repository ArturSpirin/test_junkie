import pprint

from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.FeatureAggregations import LoginSessions, Login, Dashboard

runner = Runner([Login, LoginSessions, Dashboard])
runner_metrics = runner.run()
results = runner.get_executed_suites()
tests = results[0].get_test_objects()
pprint.pprint(results[0].metrics.get_metrics())
for test in results[0].get_test_objects():
    print(test.get_function_name())
    pprint.pprint(test.metrics.get_metrics())


def test_class_metrics():

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics)


def test_test_metrics():
    for test in tests:
        metrics = test.metrics.get_metrics()["None"]["None"]
        QualityManager.check_test_metrics(metrics)


def test_advanced_aggregation_metrics():
    metrics = runner_metrics.get_report_by_features()
    dashboard_report = metrics["Dashboard"]["Charts"]
    login_auth_report = metrics["Login"]["Authentication"]
    login_input_report = metrics["Login"]["Login Inputs"]
    login_session_report = metrics["Login"]["Session Timeout"]
    reports = [dashboard_report, login_auth_report, login_input_report, login_session_report]
    for report in reports:
        assert report[TestCategory.CANCEL] == 0
        assert report[TestCategory.ERROR] == 0
        assert len(report["exceptions"]) == 0
        assert len(report["performance"]) == 2
        assert report[TestCategory.FAIL] == 0
        assert report[TestCategory.IGNORE] == 0
        assert report[TestCategory.SKIP] == 0
        assert report["retries"] == [1, 1]
        assert report["total"] == 2


def test_basic_aggregation_metrics():
    metrics = runner_metrics.get_basic_report()["tests"]
    assert metrics["total"] == 8
    assert metrics[TestCategory.SUCCESS] == 8
    assert metrics[TestCategory.FAIL] == 0
    assert metrics[TestCategory.ERROR] == 0
    assert metrics[TestCategory.IGNORE] == 0
    assert metrics[TestCategory.SKIP] == 0
    assert metrics[TestCategory.CANCEL] == 0
