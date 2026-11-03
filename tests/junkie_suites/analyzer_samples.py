"""
Traceback samples and expectations for the report Analyzer, shared by the pytest and TJ test paths.
"""
import difflib
import random
from contextlib import contextmanager

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


def numbered_tb(n):
    # the same failure from different tests: only line numbers and values differ
    return ('Traceback (most recent call last):\n  File "suite.py", line {0}, in test_case_{0}\n'
            '    assert cart.total == {1}\nAssertionError: expected {1}, got {2}\n').format(n, n * 3, n * 7)


def anagrams(count, seed=1):
    # same characters, shuffled: they pass difflib's quick filters and fail the full ratio
    rnd = random.Random(seed)
    chars = list(ASSERTION_TB + UNRELATED_TB)
    shuffled = set()
    while len(shuffled) < count:
        rnd.shuffle(chars)
        shuffled.add("".join(chars))
    return sorted(shuffled)


@contextmanager
def counting_ratio():
    calls = [0]
    original = difflib.SequenceMatcher.ratio

    def ratio(self):
        calls[0] += 1
        return original(self)

    difflib.SequenceMatcher.ratio = ratio
    try:
        yield calls
    finally:
        difflib.SequenceMatcher.ratio = original


@contextmanager
def analyzer_limits(**values):
    missing = object()
    old = {name: getattr(Analyzer, name, missing) for name in values}
    for name, value in values.items():
        setattr(Analyzer, name, value)
    try:
        yield
    finally:
        for name, value in old.items():
            if value is missing:
                delattr(Analyzer, name)
            else:
                setattr(Analyzer, name, value)


def run_scaling_checks():
    """
    Similar-traceback grouping stays bounded on failure-heavy runs (it used to compare every pair)
    """
    # 60 tests failing the same way with different numbers: one group, and masking spares difflib
    with counting_ratio() as calls:
        shared = shared_insights(analyzer_with([(n, [numbered_tb(n)]) for n in range(1, 61)]))
    assert len(shared) == 1 and shared[0]["test_ids"] == list(range(1, 61)), [s["test_ids"] for s in shared]
    assert shared[0]["text"] == "60 test failures share a similar traceback."
    assert calls[0] <= 10, calls[0]

    # run-wide cap on full comparisons, and the report says it stopped
    with analyzer_limits(MAX_COMPARISONS=50), counting_ratio() as calls:
        analyzer = analyzer_with([(n, [tb]) for n, tb in enumerate(anagrams(100), start=1)])
        stopped = [t for t in texts(analyzer) if t.startswith("Similar-traceback grouping stopped")]
    assert calls[0] <= 50, calls[0]
    assert len(stopped) == 1 and stopped[0].startswith(
        "Similar-traceback grouping stopped after 50 comparisons; "), stopped

    # each new form is compared with at most MAX_CANDIDATES groups
    with analyzer_limits(MAX_CANDIDATES=3), counting_ratio() as calls:
        analyzer = Analyzer()
        for n, tb in enumerate(anagrams(20, seed=2), start=1):
            before = calls[0]
            analyzer.analyze(n, [tb], [1.0])
            assert calls[0] - before <= 3, (n, calls[0] - before)

    # one test failing twice in a similar way is not a group
    assert shared_insights(analyzer_with([(1, [ASSERTION_TB, ASSERTION_TB_VARIANT])])) == []

    # a mostly-numeric traceback doesn't join another just because the numbers mask the same
    assert not Analyzer.is_similar("404", "500")
    assert shared_insights(analyzer_with([(1, ["404"]), (2, ["500"])])) == []


def run_checks():
    """
    Every assertion the pytest and TJ paths make, in one place
    """
    # identical tracebacks are deliberately NOT grouped - only near-identical ones are
    assert shared_insights(analyzer_with([(1, [ASSERTION_TB]), (2, [ASSERTION_TB]), (3, [ASSERTION_TB])])) == []

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
