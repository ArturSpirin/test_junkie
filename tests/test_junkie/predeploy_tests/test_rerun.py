from test_junkie.constants import TestCategory
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner
from tests.junkie_suites.RerunSuite import RerunSuite


@Suite()
class RerunTestSuite:

    @test()
    def rerunning_same_suite_with_different_tags(self):
        first_report = Runner([RerunSuite]).run(tag_config={"run_on_match_any": ["a"]}) \
            .get_basic_report()["tests"]
        assert first_report[TestCategory.SUCCESS] == 1
        assert first_report[TestCategory.SKIP] == 1

        second_report = Runner([RerunSuite]).run(tag_config={"run_on_match_any": ["b"]}) \
            .get_basic_report()["tests"]
        assert second_report[TestCategory.SUCCESS] == 1
        assert second_report[TestCategory.SKIP] == 1
