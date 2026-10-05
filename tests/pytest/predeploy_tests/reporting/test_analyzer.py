from tests.junkie_suites import analyzer_samples


def test_report_insights():
    # identical tracebacks used to be filed under "exact", which nothing read - so N tests failing on the same
    # line produced no "share a similar traceback" insight
    analyzer_samples.run_checks()
