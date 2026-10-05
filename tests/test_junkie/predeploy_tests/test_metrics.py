from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test, beforeClass
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.FeatureAggregations import LoginSessions, Login, Dashboard


@Suite()
class MetricsAggregationTestSuite:

    _runner_metrics = None
    _results = None
    _tests = None

    @beforeClass()
    def setup(self):
        runner = Runner([Login, LoginSessions, Dashboard])
        MetricsAggregationTestSuite._runner_metrics = runner.run()
        MetricsAggregationTestSuite._results = runner.get_executed_suites()
        MetricsAggregationTestSuite._tests = MetricsAggregationTestSuite._results[0].get_test_objects()

    @test()
    def class_metrics(self):
        metrics = MetricsAggregationTestSuite._results[0].metrics.get_metrics()
        QualityManager.check_class_metrics(metrics)

    @test()
    def test_metrics(self):
        for t in MetricsAggregationTestSuite._tests:
            metrics = t.metrics.get_metrics()["None"]["None"]
            QualityManager.check_test_metrics(metrics)

    @test()
    def advanced_aggregation_by_features(self):
        metrics = MetricsAggregationTestSuite._runner_metrics.get_report_by_features()
        for feature, components in [("Dashboard", "Charts"), ("Login", "Authentication"),
                                     ("Login", "Login Inputs"), ("Login", "Session Timeout")]:
            report = metrics[feature][components]
            assert report[TestCategory.CANCEL] == 0
            assert report[TestCategory.ERROR] == 0
            assert len(report["exceptions"]) == 0
            assert len(report["performance"]) == 2
            assert report[TestCategory.FAIL] == 0
            assert report[TestCategory.IGNORE] == 0
            assert report[TestCategory.SKIP] == 0
            assert report["retries"] == [1, 1]
            assert report["total"] == 2

    @test()
    def basic_aggregation(self):
        metrics = MetricsAggregationTestSuite._runner_metrics.get_basic_report()["tests"]
        assert metrics["total"] == 8
        assert metrics[TestCategory.SUCCESS] == 8
        assert metrics[TestCategory.FAIL] == 0
        assert metrics[TestCategory.ERROR] == 0
        assert metrics[TestCategory.IGNORE] == 0
        assert metrics[TestCategory.SKIP] == 0
        assert metrics[TestCategory.CANCEL] == 0

    @test()
    def basic_report_skips_tests_with_no_final_status(self):
        runner_metrics = MetricsAggregationTestSuite._runner_metrics
        tests = MetricsAggregationTestSuite._tests
        baseline_total = runner_metrics.get_basic_report()["tests"]["total"]

        tampered_test = tests[0]
        test_metrics = tampered_test.metrics.get_metrics()
        class_param = list(test_metrics.keys())[0]
        param = list(test_metrics[class_param].keys())[0]
        original_status = test_metrics[class_param][param]["status"]
        test_metrics[class_param][param]["status"] = None
        try:
            report = runner_metrics.get_basic_report()["tests"]
            assert report["total"] == baseline_total - 1
            runner_metrics.get_report_by_suite()
        finally:
            test_metrics[class_param][param]["status"] = original_status

