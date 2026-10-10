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


@Suite()
class ColoredFailureSuite:

    @test()
    def colored_assert(self):
        from test_junkie.meta import Meta
        Meta.update(note="bell\x07here")
        assert False, "\x1b[31mexpected 200\x1b[0m got 500"


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
        assert "const RESOURCES_ENABLED = true;" in html


def report_inlines_its_assets():
    # the CSS and JS ship as package data (reporter/assets) since 0.9a5 - the report must still be one
    # self-contained file
    import test_junkie.reporter
    _, html = _report(VariantsSuite)
    assets = os.path.join(os.path.dirname(test_junkie.reporter.__file__), "assets")
    for name in ("report.css", "report.js"):
        with open(os.path.join(assets, name), encoding="utf-8") as doc:
            assert doc.read() in html, name
    assert "const RESOURCES_ENABLED = false;" in html  # no resource monitoring in this run
    assert html.count("<script>") == 1 and html.count("<style>") == 1


def reports_into_folders_that_dont_exist_yet():
    """
    html_report="reports/" (a folder) used to fail with FileNotFoundError when the folder didn't exist; the JSON
    report already created it
    """
    from test_junkie.runner import Runner
    import shutil
    folder = tempfile.mkdtemp()
    try:
        out = os.path.join(folder, "new", "reports") + os.sep
        Runner([VariantsSuite], html_report=out, xml_report=out, json_report=out).run(quiet=True)
        for name in ("report.html", "report.xml", "report.json"):
            assert os.path.isfile(os.path.join(out, name)), os.listdir(folder)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def xml_report_stays_valid_with_control_characters():
    """
    A colored assertion message (ANSI codes) or a control character in meta made report.xml invalid, and every
    later run into the same file then failed to write it
    """
    from test_junkie.runner import Runner
    from xml.etree.ElementTree import parse
    path = os.path.join(tempfile.mkdtemp(), "report.xml")
    for _ in range(2):  # the second run merges into the file the first one wrote
        Runner([ColoredFailureSuite], xml_report=path).run(quiet=True)
        root = parse(path).getroot()
    failures = [f for f in root.iter("failure")]
    assert len(failures) == 2 and failures[0].get("message") == "expected 200 got 500", [f.attrib for f in failures]
    notes = [p.get("value") for p in root.iter("property") if p.get("name") == "note"]
    assert notes == ["bellhere", "bellhere"], notes


CHECKS = [report_keeps_tests_with_uncopyable_exceptions, report_variants_and_parameters,
          report_handles_a_suite_that_never_ran, report_resource_data_and_long_runtimes,
          report_inlines_its_assets, reports_into_folders_that_dont_exist_yet,
          xml_report_stays_valid_with_control_characters]
