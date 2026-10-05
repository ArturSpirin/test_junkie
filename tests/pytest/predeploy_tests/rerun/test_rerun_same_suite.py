from test_junkie.constants import TestCategory
from test_junkie.runner import Runner
from tests.junkie_suites.RerunSuite import RerunSuite


def test_rerunning_same_suite_with_different_tags_executes_fresh_each_time():
    # ticket #43 - rerunning the same suite with a different tag_config used to reuse run #1's results
    first_report = Runner([RerunSuite]).run(tag_config={"run_on_match_any": ["a"]}) \
        .get_basic_report()["tests"]
    assert first_report[TestCategory.SUCCESS] == 1  # tagged "a" ran
    assert first_report[TestCategory.SKIP] == 1      # tagged "b" skipped

    second_report = Runner([RerunSuite]).run(tag_config={"run_on_match_any": ["b"]}) \
        .get_basic_report()["tests"]
    assert second_report[TestCategory.SUCCESS] == 1  # tagged "b" must actually run this time...
    assert second_report[TestCategory.SKIP] == 1      # ...not reuse tagged "a"/"b" results from run #1
