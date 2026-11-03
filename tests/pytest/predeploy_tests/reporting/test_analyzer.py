from tests.junkie_suites import analyzer_samples


def test_report_insights():
    # identical tracebacks used to be filed under "exact", which nothing read - so N tests failing on the same
    # line produced no "share a similar traceback" insight
    analyzer_samples.run_checks()


def test_similar_grouping_scales():
    # every new traceback was compared with every known one: 446 s for 300 failures (TASK-1281)
    analyzer_samples.run_scaling_checks()
