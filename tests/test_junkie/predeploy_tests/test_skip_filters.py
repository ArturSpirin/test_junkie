from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.QualityManager import QualityManager
from tests.junkie_suites.SkipSuite import SkipSuiteAdvanced
from tests.junkie_suites.SkipSuites import SkipComponent, SkipFeature, SkipOwner, SkipTests


@Suite()
class SkipFilterTestSuite:

    @test()
    def skip_by_skip_value(self):
        runner = Runner([SkipSuiteAdvanced])
        aggregator = runner.run()
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 4
        assert metrics[TestCategory.SKIP] == 4
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")

    @test()
    def skip_by_component(self):
        runner = Runner([SkipComponent])
        aggregator = runner.run(components=["Auth API"])
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 1
        assert metrics[TestCategory.SKIP] == 2
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")

    @test()
    def skip_by_feature(self):
        runner = Runner([SkipFeature])
        aggregator = runner.run(features=["Login"])
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 3
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")

    @test()
    def skip_by_owner(self):
        runner = Runner([SkipOwner])
        aggregator = runner.run(owners=["Jane Doe"])
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 1
        assert metrics[TestCategory.SKIP] == 2
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")

    @test()
    def skip_by_tests_filter(self):
        runner = Runner([SkipTests])
        aggregator = runner.run(tests=[SkipTests.test_1, SkipTests.test_2])
        metrics = aggregator.get_basic_report()["tests"]
        assert metrics[TestCategory.SUCCESS] == 2
        assert metrics[TestCategory.SKIP] == 1
        suites = runner.get_executed_suites()
        QualityManager.check_class_metrics(suites[0].metrics.get_metrics(), expected_status="success")
