import os
import sys
import traceback

from test_junkie.constants import TestCategory
from test_junkie.debugger import LogJunkie


class XmlReporter:

    @staticmethod
    def __error_attrs(error):
        if not isinstance(error, BaseException):
            return {}
        return {"type": type(error).__name__, "message": str(error).split("\n")[0]}

    @staticmethod
    def __add_runs(test, test_status, data):
        """
        Surefire's layout for retried tests, which CI tools and flaky-test trackers read. A test that passed after
        failing gets a <flakyFailure>/<flakyError> per failed run. A test that never passed gets <failure> for its
        first run and a <rerunFailure>/<rerunError> for each retry that failed too.
        """
        from xml.etree.ElementTree import SubElement
        statuses = data.get("statuses") or []
        errors = data.get("exceptions") or []
        traces = data.get("tracebacks") or []
        bad = (TestCategory.FAIL, TestCategory.ERROR)

        def run(tag, index):
            element = SubElement(test, tag, **XmlReporter.__error_attrs(errors[index] if index < len(errors) else None))
            trace = traces[index] if index < len(traces) else None
            if trace:
                SubElement(element, "stackTrace").text = str(trace)
            return element

        if test_status != "failure":
            for index, status in enumerate(statuses[:-1]):
                if status in bad:
                    run("flakyFailure" if status == TestCategory.FAIL else "flakyError", index)
            return
        if statuses:
            failure = run("failure", 0)
            if failure.get("type") is None:
                failure.set("type", "failure")
            for index, status in enumerate(statuses[1:], 1):
                if status in bad:
                    run("rerunFailure" if status == TestCategory.FAIL else "rerunError", index)
        else:  # never ran (ignored, skipped, cancelled before starting)
            SubElement(test, "failure", type="failure")

    @staticmethod
    def create_xml_report(write_file, suites):

        def __update_tag_stats(tag, status):

            tag.set("tests", str(int(tag.get("tests")) + 1))
            if status == TestCategory.SUCCESS:
                tag.set("passed", str(int(tag.get("passed")) + 1))
            else:
                tag.set("failures", str(int(tag.get("failures")) + 1))
            return tag

        if write_file is not None:
            try:
                import os
                from xml.etree.ElementTree import ElementTree, Element, SubElement, parse

                # appends to an existing report. The file used to be rewritten after every single test - quadratic
                # for big runs - and each test searched all suites by name
                root = parse(write_file).getroot() if os.path.exists(write_file) else Element("root")
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

                                test_status = param_data["status"]
                                if test_status != TestCategory.SUCCESS:
                                    test_status = "failure"

                                suite = suites_by_name.get(test_suite)
                                if suite is None:
                                    suite = SubElement(root, "testsuite", name=test_suite,
                                                       tests="0", passed="0", failures="0")
                                    suites_by_name[test_suite] = suite
                                __update_tag_stats(suite, test_status)
                                test = SubElement(suite, "testcase", name=str(test_name), status=str(test_status))
                                XmlReporter.__add_runs(test, test_status, param_data)
                os.makedirs(os.path.dirname(os.path.abspath(write_file)), exist_ok=True)
                ElementTree(root).write(write_file)
            except Exception:
                trace = traceback.format_exc()
                print("[WARNING] Failed to write XML report to: {}\n{}".format(write_file, trace),
                      file=sys.stderr)
                LogJunkie.error(trace)
