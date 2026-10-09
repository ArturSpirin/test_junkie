import os
import sys
import traceback

from test_junkie.constants import TestCategory
from test_junkie.debugger import LogJunkie


class XmlReporter:

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
                                if test_status == "failure":
                                    SubElement(test, "failure", type="failure")
                os.makedirs(os.path.dirname(os.path.abspath(write_file)), exist_ok=True)
                ElementTree(root).write(write_file)
            except Exception:
                trace = traceback.format_exc()
                print("[WARNING] Failed to write XML report to: {}\n{}".format(write_file, trace),
                      file=sys.stderr)
                LogJunkie.error(trace)
