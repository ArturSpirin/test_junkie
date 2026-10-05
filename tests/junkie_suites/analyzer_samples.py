"""
Traceback samples and expectations for the report Analyzer, shared by the pytest and TJ test paths.
"""
from test_junkie.reporter.analyzer import Analyzer

ASSERTION_TB = ('Traceback (most recent call last):\n  File "suite.py", line 12, in test_login\n'
                '    assert page.title == "Dashboard"\nAssertionError: expected Dashboard, got Login\n')
# same failure, different values - "similar", not identical
ASSERTION_TB_VARIANT = ASSERTION_TB.replace("got Login", "got Error")
UNRELATED_TB = ('Traceback (most recent call last):\n  File "db.py", line 88, in connect\n'
                '    raise ConnectionRefusedError(111)\nConnectionRefusedError: [Errno 111] Connection refused\n')


def texts(analyzer):
    return [insight["text"] for insight in analyzer.structured_analysis]


def shared_insights(analyzer):
    return [insight for insight in analyzer.structured_analysis if "share a similar traceback" in insight["text"]]


def analyzer_with(failures, **kwargs):
    """
    :param failures: LIST of (test_id, LIST of tracebacks per attempt) - None traceback = passed attempt
    """
    analyzer = Analyzer(**kwargs)
    for test_id, tracebacks in failures:
        analyzer.analyze(test_id, tracebacks, [1.0] * len(tracebacks))
    return analyzer


def run_checks():
    """
    Every assertion the pytest and TJ paths make, in one place
    """
    # identical tracebacks across 3 tests - used to produce no "share" insight at all
    shared = shared_insights(analyzer_with([(1, [ASSERTION_TB]), (2, [ASSERTION_TB]), (3, [ASSERTION_TB])]))
    assert [(i["text"], i["test_ids"]) for i in shared] == [("3 test failures share a similar traceback.", [1, 2, 3])]

    # near-identical still groups
    shared = shared_insights(analyzer_with([(1, [ASSERTION_TB]), (2, [ASSERTION_TB_VARIANT])]))
    assert len(shared) == 1 and sorted(shared[0]["test_ids"]) == [1, 2]

    # unrelated failures don't
    analyzer = analyzer_with([(1, [ASSERTION_TB]), (2, [UNRELATED_TB])])
    assert shared_insights(analyzer) == []
    assert "There are 2 unique tracebacks across all unsuccessful tests." in texts(analyzer)

    # nothing failed
    assert texts(analyzer_with([(1, [None])])) == [
        "All of your tests are stable and no time was lost on retries."]

    # a retry: first attempt failed, second passed - the second attempt's time counts as lost
    analyzer = Analyzer()
    analyzer.analyze(1, [ASSERTION_TB, None], [1.0, 2.5])
    assert "Total of 1 retries cost 2.5 seconds." in texts(analyzer)

    # resource monitoring messages
    spiking = Analyzer(monitoring_enabled=True, multi_threading_enabled=True)
    for _ in range(11):
        spiking.update_resources(cpu=99, mem=75)
    assert any(t.startswith("CPU spiked 11 times") and t.endswith("and/or reducing thread allocation.")
               for t in texts(spiking))
    assert "Consider enabling multi-threading to speed up test execution." in texts(
        Analyzer(monitoring_enabled=True))
    assert "More CPU resources can be utilized; consider allocating more threads." in texts(
        Analyzer(monitoring_enabled=True, multi_threading_enabled=True))

    assert Analyzer.is_similar(ASSERTION_TB, ASSERTION_TB_VARIANT)
    assert not Analyzer.is_similar(ASSERTION_TB, UNRELATED_TB)
