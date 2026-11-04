import os
import re
import sys
import traceback

from test_junkie.constants import TestCategory
from test_junkie.debugger import LogJunkie
from test_junkie.meta import report_text
from test_junkie.params import param_key

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_NOT_XML = re.compile("[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]")


def _xml_safe(text):
    """Drops color codes and the characters XML 1.0 can't hold, so a colored assertion can't make the file invalid"""
    return _NOT_XML.sub("", _ANSI.sub("", str(text)))


def _meta_line(key, value):
    """One `key: value` line of a test's <system-out>; backslashes, CR and LF are escaped so each entry stays one line"""
    def flat(text):
        return _xml_safe(text).replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")
    return "{}: {}".format(flat(key), flat(report_text(value)))


LEGACY_WARNING = ("xml_report_legacy writes the old report.xml layout (<root>, passed= and status= attributes, "
                  "<properties> in <testcase>), which JUnit tools like Jenkins reject. It will be removed in "
                  "Test Junkie 2.0. See {}")

# a test's final status -> its JUnit element (None: passed); ignore (setup broke) is an error, cancel never ran
_JUNIT = {TestCategory.SUCCESS: None, TestCategory.FAIL: "failure", TestCategory.ERROR: "error",
          TestCategory.IGNORE: "error", TestCategory.SKIP: "skipped", TestCategory.CANCEL: "skipped"}
# the <testsuite> attribute each element is counted in
_COUNT = {"failure": "failures", "error": "errors", "skipped": "skipped"}


def _junit_kind(status):
    """The JUnit element for a final status; an unknown status is a failure, as it always was"""
    return _JUNIT.get(status, "failure")


class XmlReporter:

    @staticmethod
    def __case_name(test_name, data):
        """The test's name with its parameters, like the console: login[suite: admin, 2]"""
        parts = []
        if data.get("class_param") is not None:
            parts.append("suite: {}".format(param_key(data["class_param"])))
        if data.get("param") is not None:
            parts.append(param_key(data["param"]))
        return "{}[{}]".format(test_name, ", ".join(parts)) if parts else str(test_name)

    @staticmethod
    def __error_attrs(error):
        if not isinstance(error, BaseException):
            return {}
        return {"type": type(error).__name__, "message": _xml_safe(str(error).split("\n")[0])}

    @staticmethod
    def __add_runs(test, kind, data):
        """
        Surefire's layout for retried tests, which CI tools and flaky-test trackers read. A test that passed after
        failing gets a <flakyFailure>/<flakyError> per failed run. A test that failed or errored gets <failure> or
        <error> by its final status, with the exception of its first run with that status, and a
        <rerunFailure>/<rerunError> for each other run that failed too. A skipped or cancelled test gets <skipped/>.
        """
        from xml.etree.ElementTree import SubElement
        statuses = data.get("statuses") or []
        errors = data.get("exceptions") or []
        traces = data.get("tracebacks") or []
        bad = (TestCategory.FAIL, TestCategory.ERROR)

        def run(tag, index):
            element = SubElement(test, tag, **XmlReporter.__error_attrs(errors[index] if index < len(errors) else None))
            if element.get("type") is None:  # required on flaky*/rerun* (junit-10 rerunType), no exception recorded
                element.set("type", "error" if tag.lower().endswith("error") else "failure")
            trace = traces[index] if index < len(traces) else None
            if trace:
                if tag in ("failure", "error"):  # Surefire: these hold the trace as text, <stackTrace> is for flaky*/rerun*
                    element.text = _xml_safe(trace)
                else:
                    SubElement(element, "stackTrace").text = _xml_safe(trace)
            return element

        if kind is None:
            for index, status in enumerate(statuses[:-1]):
                if status in bad:
                    run("flakyFailure" if status == TestCategory.FAIL else "flakyError", index)
            return
        if kind == "skipped":  # junit-10: a <testcase> holds one of skipped, error or failure
            SubElement(test, "skipped")
            return
        if not statuses:  # never ran (ignored before starting)
            SubElement(test, kind, type=kind)
            return
        same = TestCategory.FAIL if kind == "failure" else TestCategory.ERROR
        main = next((index for index, status in enumerate(statuses) if status == same), 0)
        run(kind, main)
        for index, status in enumerate(statuses):
            if index != main and status in bad:
                run("rerunFailure" if status == TestCategory.FAIL else "rerunError", index)

    @staticmethod
    def __properties_to_system_out(case):
        """
        junit-10 has no <properties> in <testcase>: an old or legacy case's meta becomes the `key: value` lines a new
        run writes, after any <system-out> text the case already had. The values go through report_text like a new
        run's, so one over VALUE_LIMIT is cut the same way
        """
        lines = []
        for properties in case.findall("properties"):
            lines.extend(_meta_line(prop.get("name", ""), prop.get("value", "")) for prop in properties.iter("property"))
            case.remove(properties)
        if not lines:
            return
        from xml.etree.ElementTree import SubElement
        outputs = case.findall("system-out")
        for output in outputs:
            case.remove(output)
        earlier = [output.text for output in outputs if output.text]
        SubElement(case, "system-out").text = "\n".join(earlier + lines)

    @staticmethod
    def __normalise(root, legacy):
        """
        Brings a report being appended to into this run's layout. junit-10 (default): <testsuites> root, errors and
        skipped on every suite, no passed/status, case meta in <system-out>. Legacy keeps the file's root as it is and puts passed back
        """
        if not legacy:
            if root.tag == "root":
                root.tag = "testsuites"
            for case in root.iter("testcase"):
                case.attrib.pop("status", None)
                XmlReporter.__properties_to_system_out(case)
        for suite in root.iter("testsuite"):
            suite.attrib.setdefault("errors", "0")
            suite.attrib.setdefault("skipped", "0")
            if legacy:
                suite.attrib.setdefault("passed", str(int(suite.get("tests", 0)) - int(suite.get("failures", 0))
                                                      - int(suite.get("errors")) - int(suite.get("skipped"))))
            else:
                suite.attrib.pop("passed", None)

    @staticmethod
    def __set_totals(root):
        """junit-10's <testsuites> totals: the sums over its suites"""
        if root.tag != "testsuites":
            return
        suites = list(root.iter("testsuite"))
        for name in ("tests", "failures", "errors"):
            root.set(name, str(sum(int(suite.get(name, 0)) for suite in suites)))

    @staticmethod
    def create_xml_report(write_file, suites, legacy=False):
        """
        Writes (or appends to) a JUnit XML report that validates against junit-10.xsd (Jenkins xUnit). A test's meta
        goes in its <system-out>, one `key: value` line per entry. legacy=True (xml_report_legacy) writes the old
        layout instead, until 2.0: <root>, passed=/status= attributes and <properties> in <testcase>. Legacy brings
        back the old shape only: in both layouts an error or ignored test is an <error>, a skipped or cancelled test
        a <skipped/>, each counted in errors/skipped rather than failures
        """

        def __update_tag_stats(tag, kind):

            tag.set("tests", str(int(tag.get("tests")) + 1))
            if kind is None:
                if legacy:
                    tag.set("passed", str(int(tag.get("passed")) + 1))
            else:
                count = _COUNT[kind]
                tag.set(count, str(int(tag.get(count)) + 1))
            return tag

        if write_file is not None:
            if legacy:
                import warnings
                from test_junkie.constants import DocumentationLinks
                # FutureWarning: Python hides a DeprecationWarning raised outside __main__, so users would never see it
                warnings.warn(LEGACY_WARNING.format(DocumentationLinks.XML_REPORT), FutureWarning, stacklevel=2)
            try:
                import os
                from xml.etree.ElementTree import ElementTree, Element, SubElement, parse

                # appends to an existing report. The file used to be rewritten after every single test - quadratic
                # for big runs - and each test searched all suites by name
                if os.path.exists(write_file):
                    root = parse(write_file).getroot()
                    XmlReporter.__normalise(root, legacy)
                else:
                    root = Element("root" if legacy else "testsuites")
                suites_by_name = {}
                for suite in root.iter("testsuite"):
                    suites_by_name.setdefault(suite.attrib["name"], suite)

                for suite_object in suites:

                    test_suite = suite_object.get_class_name()
                    tests = suite_object.get_test_objects()

                    for test_object in tests:

                        test_name = test_object.get_function_name()
                        test_metrics = test_object.metrics.get_metrics()

                        for class_param, class_param_data in test_metrics.items():
                            for param, param_data in class_param_data.items():

                                kind = _junit_kind(param_data["status"])
                                test_status = "success" if kind is None else "failure"  # legacy status=

                                suite = suites_by_name.get(test_suite)
                                if suite is None:
                                    suite = SubElement(root, "testsuite", name=_xml_safe(test_suite), tests="0")
                                    if legacy:
                                        suite.set("passed", "0")
                                    suite.set("failures", "0")
                                    suite.set("errors", "0")
                                    suite.set("skipped", "0")
                                    suites_by_name[test_suite] = suite
                                __update_tag_stats(suite, kind)
                                test = SubElement(suite, "testcase", name=_xml_safe(XmlReporter.__case_name(test_name, param_data)),
                                                  classname=_xml_safe(test_suite))
                                if legacy:
                                    test.set("status", str(test_status))
                                runtimes = param_data.get("performance") or []
                                if runtimes:  # Surefire: the first run's time for a failure or error, else the last run's
                                    seconds = runtimes[0] if kind in ("failure", "error") else runtimes[-1]
                                    test.set("time", "{:.3f}".format(seconds or 0))
                                values = test_object.get_meta(param_data.get("param"), param_data.get("class_param"),
                                                              copy_of_meta=True)
                                if values and legacy:
                                    properties = SubElement(test, "properties")
                                    for key, value in values.items():
                                        SubElement(properties, "property", name=_xml_safe(key), value=_xml_safe(report_text(value)))
                                XmlReporter.__add_runs(test, kind, param_data)
                                if values and not legacy:  # junit-10 has no <properties> in <testcase>
                                    SubElement(test, "system-out").text = "\n".join(
                                        _meta_line(key, value) for key, value in values.items())
                XmlReporter.__set_totals(root)
                os.makedirs(os.path.dirname(os.path.abspath(write_file)), exist_ok=True)
                ElementTree(root).write(write_file)
            except Exception:
                trace = traceback.format_exc()
                print("[WARNING] Failed to write XML report to: {}\n{}".format(write_file, trace),
                      file=sys.stderr)
                LogJunkie.error(trace)
