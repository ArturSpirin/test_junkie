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
    notes = [out.text for out in root.iter("system-out")]
    assert notes == ["note: bellhere", "note: bellhere"], notes


@Suite()
class MetaSuite:

    @test(parameters=[1, 2])
    def with_meta(self, parameter):
        from test_junkie.meta import Meta
        Meta.update(page=parameter, note="line one\nline two", path="C:\\data")
        assert parameter == 1, "fails for 2"

    @test()
    def without_meta(self):
        pass


def _xml(*suites, **run_kwargs):
    """The path of a report.xml written by a run of these suites"""
    from test_junkie.runner import Runner
    path = run_kwargs.pop("path", None) or os.path.join(tempfile.mkdtemp(), "report.xml")
    Runner(list(suites), quiet=True, xml_report=path).run(**run_kwargs)
    return path


def _junit_10_errors(path):
    from tests.stress import report_check
    result = report_check.validate_xml(path)
    return result["examples"] if not result["valid"] else None


def xml_report_has_testsuites_root_and_totals():
    # junit-10 (Jenkins xUnit): <testsuites> root, errors on every suite, no passed=/status= (TASK-1315)
    from xml.etree.ElementTree import parse
    root = parse(_xml(VariantsSuite, ColoredFailureSuite)).getroot()
    suites = list(root.iter("testsuite"))
    assert root.tag == "testsuites" and len(suites) == 2, root.tag
    for name in ("tests", "failures", "errors"):
        assert root.get(name) == str(sum(int(suite.get(name)) for suite in suites)), (name, root.attrib)
    assert root.get("tests") == "5" and root.get("failures") == "2", root.attrib
    assert all(suite.get("errors") is not None and suite.get("passed") is None for suite in suites), \
        [suite.attrib for suite in suites]
    assert all(case.get("status") is None for case in root.iter("testcase"))


def xml_report_with_meta_validates():
    # meta used to go in <properties> inside <testcase>, which junit-10 doesn't allow: now <system-out>, one
    # `key: value` line per entry, newlines and backslashes escaped so each entry stays one line
    from xml.etree.ElementTree import parse
    path = _xml(MetaSuite)
    assert _junit_10_errors(path) is None, _junit_10_errors(path)
    cases = {case.get("name"): case for case in parse(path).getroot().iter("testcase")}
    assert cases["with_meta[2]"].find("system-out").text.split("\n") == \
        ["page: 2", "note: line one\\nline two", "path: C:\\\\data"], cases["with_meta[2]"].find("system-out").text
    assert cases["without_meta"].find("system-out") is None and cases["with_meta[1]"].find("properties") is None


def xml_report_legacy_keeps_old_attributes():
    # xml_report_legacy=True: the old layout until 2.0, with a FutureWarning (shown by default, unlike a
    # DeprecationWarning raised outside __main__)
    import warnings
    from xml.etree.ElementTree import parse
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        path = _xml(MetaSuite, xml_report_legacy=True)
    assert [w for w in caught if issubclass(w.category, FutureWarning) and "2.0" in str(w.message)], \
        [str(w.message) for w in caught]
    root = parse(path).getroot()
    suite = root.find("testsuite")
    assert root.tag == "root" and suite.get("passed") == "2" and suite.get("failures") == "1", suite.attrib
    cases = {case.get("name"): case for case in root.iter("testcase")}
    assert cases["with_meta[1]"].get("status") == "success" and cases["with_meta[2]"].get("status") == "failure"
    properties = {p.get("name"): p.get("value") for p in cases["with_meta[2]"].find("properties")}
    assert properties == {"page": "2", "note": "line one\nline two", "path": "C:\\data"}, properties
    assert cases["with_meta[2]"].find("system-out") is None


def xml_report_rerun_without_exception_has_type():
    # junit-10's rerunType needs type=: a run with no exception recorded used to give flaky*/rerun* none
    from test_junkie.constants import TestCategory
    from test_junkie.reporter.xml_reporter import XmlReporter
    from xml.etree.ElementTree import Element
    add_runs = getattr(XmlReporter, "_XmlReporter__add_runs")
    failed, flaky = Element("testcase"), Element("testcase")
    add_runs(failed, "failure", {"statuses": [TestCategory.FAIL, TestCategory.ERROR, TestCategory.FAIL]})
    add_runs(flaky, TestCategory.SUCCESS, {"statuses": [TestCategory.ERROR, TestCategory.FAIL, TestCategory.SUCCESS],
                                           "exceptions": [None, "not an exception"]})
    assert [(e.tag, e.get("type")) for e in failed] == [("failure", "failure"), ("rerunError", "error"),
                                                        ("rerunFailure", "failure")], [e.attrib for e in failed]
    assert [(e.tag, e.get("type")) for e in flaky] == [("flakyError", "error"), ("flakyFailure", "failure")], \
        [e.attrib for e in flaky]


def xml_report_appends_to_old_format_file():
    # a report.xml from before TASK-1315 (<root>, passed=, status=) comes out as valid junit-10 after the next run
    from xml.etree.ElementTree import parse
    path = os.path.join(tempfile.mkdtemp(), "report.xml")
    with open(path, "w", encoding="utf-8") as doc:
        doc.write('<root><testsuite name="OldSuite" tests="2" passed="1" failures="1">'
                  '<testcase name="old_pass" classname="OldSuite" status="success" />'
                  '<testcase name="old_fail" classname="OldSuite" status="failure"><failure type="failure" />'
                  '</testcase></testsuite></root>')
    _xml(VariantsSuite, path=path)
    assert _junit_10_errors(path) is None, _junit_10_errors(path)
    root = parse(path).getroot()
    old = root.find("testsuite[@name='OldSuite']")
    assert root.tag == "testsuites" and old.get("passed") is None and old.get("errors") == "0", old.attrib
    assert root.get("tests") == "6" and root.get("failures") == "2", root.attrib
    assert all(case.get("status") is None for case in root.iter("testcase"))


CHECKS = [report_keeps_tests_with_uncopyable_exceptions, report_variants_and_parameters,
          report_handles_a_suite_that_never_ran, report_resource_data_and_long_runtimes,
          report_inlines_its_assets, reports_into_folders_that_dont_exist_yet,
          xml_report_stays_valid_with_control_characters, xml_report_has_testsuites_root_and_totals,
          xml_report_with_meta_validates, xml_report_legacy_keeps_old_attributes,
          xml_report_rerun_without_exception_has_type, xml_report_appends_to_old_format_file]
