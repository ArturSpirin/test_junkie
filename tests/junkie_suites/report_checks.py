"""
HTML report checks shared by the pytest and TJ test paths: each generates a real report and asserts on the data
embedded in it.
"""
import json
import os
import re
import tempfile
import threading

from test_junkie.decorators import Suite, test, beforeTest


class ConnectionDropped(Exception):
    """An exception carrying something that can't be deep-copied, like a client, socket or lock"""

    def __init__(self, message):
        super().__init__(message)
        self.lock = threading.Lock()


@Suite()
class UncopyableFailureSuite:

    @test()
    def passes(self):
        pass

    @test()
    def fails_with_uncopyable_exception(self):
        raise ConnectionDropped("socket closed")


class Opaque:
    """A parameter whose str() is the default <...object at 0x...> repr"""


FLAKY_VARIANT = Opaque()


@Suite()
class VariantsSuite:

    @beforeTest()
    def before_test(self):
        pass

    @test(parameters=[1, FLAKY_VARIANT])
    def mixed_variants(self, parameter):
        assert parameter is not FLAKY_VARIANT, "fails for the opaque variant only"

    @test()
    def no_component_a(self):
        pass

    @test()
    def no_component_b(self):
        pass


@Suite(skip=True)
class SkippedSuite:

    @test()
    def never_runs(self):
        pass


def _report(*suites, **run_kwargs):
    from test_junkie.runner import Runner
    path = os.path.join(tempfile.mkdtemp(), "report.html")
    runner = Runner(list(suites), quiet=True, html_report=path)
    runner.run(**run_kwargs)
    with open(path, encoding="utf-8") as doc:
        html = doc.read()
    return runner, html


def _embedded(html, name):
    return json.loads(re.search(r"const {} = (.*?);\n".format(name), html).group(1))


def report_keeps_tests_with_uncopyable_exceptions():
    # deep-copying the metrics failed and the test silently disappeared from the report
    _, html = _report(UncopyableFailureSuite)
    tests = {entry["test"]: entry for entry in _embedded(html, "TESTS")}
    assert set(tests) == {"passes", "fails_with_uncopyable_exception"}, sorted(tests)
    assert tests["fails_with_uncopyable_exception"]["status"] == "error"


def report_variants_and_parameters():
    _, html = _report(VariantsSuite)
    tests = {entry["test"]: entry for entry in _embedded(html, "TESTS")}
    details = _embedded(html, "DETAILS")
    mixed = tests["mixed_variants"]
    assert mixed["variantCount"] == 2
    assert mixed["status"] == "fail"  # one variant failed - the worst status wins
    labels = [variant["testParam"] for variant in details[str(mixed["id"])]["variants"]]
    assert "1" in labels and any(label.startswith("&lt;") and label.endswith("&gt;") for label in labels), labels
    assert tests["no_component_a"]["component"] == tests["no_component_b"]["component"] == "Not Defined"


def report_handles_a_suite_that_never_ran():
    _, html = _report(SkippedSuite, VariantsSuite)
    names = [entry["test"] for entry in _embedded(html, "TESTS")]
    assert "never_runs" not in names and "mixed_variants" in names


def report_resource_data_and_long_runtimes():
    from test_junkie.metrics import Aggregator
    from test_junkie.reporter.html_reporter import Reporter
    runner, _ = _report(VariantsSuite)
    monitoring = os.path.join(tempfile.mkdtemp(), "resources")
    with open(monitoring, "w") as doc:
        doc.write("2026-10-05 10:00:00.250000, 20.0, 40.0\n"
                  "\n"                                       # blank lines are skipped
                  "2026-10-05 10:00:01, 35.5, 41.0\n"        # timestamp without microseconds
                  "not-a-date, 50.0, 42.0\n"                 # unparseable timestamp
                  "2026-10-05 10:00:03.000001, 99.0, 43.0\n")  # peak at the far right
    for average, expected in ((4000, "01h:06m:40s"), (90, "01m:30s")):
        reporter = Reporter(monitoring_file=monitoring, aggregator=Aggregator(runner.get_executed_suites()),
                            runtime=average, multi_threading_enabled=False)
        reporter.average_runtime = average
        path = os.path.join(tempfile.mkdtemp(), "report.html")
        reporter.generate_html_report(path)
        with open(path, encoding="utf-8") as doc:
            html = doc.read()
        assert expected in html, expected
        assert "99%" in html  # CPU peak


CHECKS = [report_keeps_tests_with_uncopyable_exceptions, report_variants_and_parameters,
          report_handles_a_suite_that_never_ran, report_resource_data_and_long_runtimes]
