import json

from test_junkie.constants import DocumentationLinks, TestCategory
from test_junkie.errors import BadParameters
from test_junkie.params import param_key


def _text(value):
    return None if value is None else param_key(value)


class Rerun(object):
    """
    Tests to run again, down to the parameter: Runner.run(rerun=...) runs only these. tj run --rerun FILE reruns what
    didn't pass in a JSON report. To match parameters your own way, add() the tests and override includes()
    """

    def __init__(self):
        self.__tests = {}  # (suite name, test name) -> {(suite parameter, parameter)}, both as text
        self.source = None  # the JSON report it was read from

    def add(self, suite, test, parameter=None, suite_parameter=None):
        """
        :param suite: STRING, name of the suite class
        :param test: STRING, name of the test function
        :param parameter: the test's parameter, or its text from a JSON report
        :param suite_parameter: the suite's parameter, or its text from a JSON report
        :return: self
        """
        self.__tests.setdefault((suite, test), set()).add((_text(suite_parameter), _text(parameter)))
        return self

    @staticmethod
    def from_report(path, statuses=None):
        """
        :param path: STRING, a report written by tj run --json-report or Runner(json_report=...)
        :param statuses: LIST, results to run again. Failed, errored and ignored by default
        :return: Rerun
        """
        statuses = TestCategory.ALL_UN_SUCCESSFUL if statuses is None else statuses
        rerun = Rerun()
        rerun.source = str(path)
        try:
            with open(path, encoding="utf-8") as doc:
                report = json.load(doc)
            for suite in report["suites"]:
                for test in suite["tests"]:
                    if test["status"] in statuses:
                        rerun.add(suite["name"], test["name"], test["parameter"], test["suite_parameter"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise BadParameters("\"rerun\" needs a JSON report written by --json-report. Could not read {}: {!r}. "
                                "See documentation: {}".format(path, error, DocumentationLinks.RERUN))
        return rerun

    def includes_test(self, suite, test):
        """
        :return: BOOLEAN, True if the test runs again, with at least one of its parameters
        """
        return (suite, test) in self.__tests

    def includes(self, suite, test, parameter=None, suite_parameter=None):
        """
        Override to match parameters your own way. By default they match on their text, as reports show them
        :return: BOOLEAN, True if the test runs again with this parameter and suite parameter
        """
        return (_text(suite_parameter), _text(parameter)) in self.__tests.get((suite, test), ())

    def __len__(self):
        return len(self.__tests)

    def __str__(self):
        tests = "{} test{}".format(len(self), "" if len(self) == 1 else "s")
        return tests if self.source is None else "{} from {}".format(tests, self.source)


def parameters_to_run(rerun, test, parameters, suite_parameters, suite_parameter):
    """
    :param parameters: LIST, the test's parameters
    :param suite_parameters: LIST, the suite's parameters
    :param suite_parameter: the suite parameter the test is about to run under
    :return: LIST, the parameters the test runs again with under suite_parameter. None if the rerun includes none of
             the test's parameters - they changed since the run it repeats, so all of them run
    """
    suite, name = test.suite.get_class_name(), test.get_function_name()
    accepts = test.accepts_suite_parameters()

    def included(parameter, suite_param):
        return rerun.includes(suite, name, parameter, suite_param if accepts else None)

    if not any(included(parameter, suite_param) for suite_param in suite_parameters for parameter in parameters):
        return None
    return [parameter for parameter in parameters if included(parameter, suite_parameter)]
