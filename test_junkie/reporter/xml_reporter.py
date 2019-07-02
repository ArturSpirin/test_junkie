import traceback

from test_junkie.constants import TestCategory
from test_junkie.debugger import LogJunkie


class XmlReporter:

    @staticmethod
    def create_xml_report(write_file, suites):

        def __update_tag_stats(tag, status):

            tag.set("tests", str(int(suite.get("tests")) + 1))
            if status == TestCategory.SUCCESS:
                tag.set("passed", str(int(tag.get("passed")) + 1))
            else:
                tag.set("failures", str(int(tag.get("failures")) + 1))
            return tag

        if write_file is not None:
            try:
                import os
                from xml.etree.ElementTree import ElementTree, Element, SubElement
                import xml
                if not os.path.exists(write_file):
                    request = Element("root")
                    ElementTree(request).write(write_file)

                xml_file = xml.etree.ElementTree.parse(write_file)
                root = xml_file.getroot()

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
                                suite_found = False

                                for suite in root.iter("testsuite"):
                                    suite_found = suite.attrib["name"] == test_suite
                                    if suite_found:
                                        __update_tag_stats(suite, test_status)
                                        test = Element("testcase", name=str(test_name), status=str(test_status))
                                        if test_status == "failure":
                                            failure = Element("failure", type="failure")
                                            test.append(failure)
                                        suite.append(test)
                                        ElementTree(root).write(write_file)
                                        break

                                if not suite_found:
                                    suite = SubElement(root, "testsuite", name=test_suite,
                                                       tests="0", passed="0", failures="0")
                                    __update_tag_stats(suite, test_status)
                                    test = SubElement(suite, "testcase", name=str(test_name), status=str(test_status))
                                    if test_status == "failure":
                                        SubElement(test, "failure", type="failure")
                                    ElementTree(root).write(write_file)
            except:
                LogJunkie.error(traceback.format_exc())
