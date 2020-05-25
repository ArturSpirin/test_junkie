import collections

from test_junkie.builder import Builder
from test_junkie.constants import Undefined


class CliAudit:

    __SECTIONS = ["owners", "features", "suites", "components", "tags"]

    def __init__(self, suites, args):

        self.aggregated_data = {
                "absolute_test_count": 0,  # parameterized tests will be treated as 1 test
                "absolute_suite_count": 0,

                "context_by_features": {},
                "context_by_owners": {},
                "context_by_suites": {},
                "context_by_tags": {},
                "context_by_components": {},
                "test_roster": {},

                "parameterized_test_count": 0,
                "parameterized_suite_count": 0,
                }
        self.suites = suites
        self.exe_roster = Builder.get_execution_roster()
        self.args = args if args is not None else Undefined

    def aggregate(self):

        from test_junkie.settings import Settings

        def is_relevant(_suite=None, _test=None):

            if not _suite and not _test:
                raise Exception("Must pass in either a SuiteObject or a TestObject!")

            elif _suite and not _test:
                from test_junkie.rules import Rules
                if self.args.get("no_rules", Undefined) and _suite.get_rules().__class__ != Rules:
                    return False

                from test_junkie.listener import Listener
                if self.args.get("no_listeners", Undefined) and _suite.get_listener().__class__ != Listener:
                    return False

                if self.args.get("no_suite_retries", Undefined) and _suite.get_retry_limit() > 1:
                    return False

                if self.args.get("no_suite_meta", Undefined) and _suite.get_meta():
                    return False

                if self.args.get("no_owners", Undefined) and _suite.get_owner():
                    return False

                if self.args.get("no_features", Undefined) and _suite.get_feature():
                    return False

                if not Settings.is_undefined(self.args.get("features", Undefined)):
                    if _suite.get_feature() in self.args.get("features", Undefined):
                        return True
                    return False

            else:
                if self.args.get("no_test_retries", Undefined) and _test.get_retry_limit() > 1:
                    return False

                if self.args.get("no_test_meta", Undefined) and _suite.get_meta():
                    return False

                if self.args.get("no_owners", Undefined) and _test.get_owner():
                    return False

                if self.args.get("no_components", Undefined) and _test.get_component():
                    return False

                if self.args.get("no_tags", Undefined) and _test.get_tags():
                    return False

                if not Settings.is_undefined(self.args.get("owners", Undefined)):
                    if _test.get_owner() in self.args.get("owners", Undefined):
                        return True
                    return False

                if not Settings.is_undefined(self.args.get("components", Undefined)):
                    if _test.get_component() in self.args.get("components", Undefined):
                        return True
                    return False

                if not Settings.is_undefined(self.args.get("tags", Undefined)):
                    for tag in self.args.get("tags", Undefined):
                        if tag in _test.get_tags():
                            return True
                    return False
            return True

        for suite, suite_object in self.exe_roster.items():
            if not Settings.is_undefined(self.args):
                if not is_relevant(_suite=suite_object):
                    continue

            tests = suite_object.get_test_objects()
            self.aggregated_data["absolute_suite_count"] += 1
            if suite_object.get_parameters() != [None]:
                self.aggregated_data["parameterized_suite_count"] += 1

            feature = suite_object.get_feature()
            if feature not in self.aggregated_data["context_by_features"]:
                self.aggregated_data["context_by_features"].update({
                    feature: {"tags": {}, "owners": {}, "components": {}, "suites": {}, "total_tests": 0}})
            feature_context = self.aggregated_data["context_by_features"][feature]
            feature_context["total_tests"] += len(tests)
            feature_context["suites"].update({"{}.{}".format(suite_object.get_class_module(),
                                                             suite_object.get_class_name()): len(tests)})

            suite_context = {"total_tests": len(tests),
                             "tags": {},
                             "owners": {},
                             "components": {},
                             "feature": feature}

            self.aggregated_data["absolute_test_count"] += len(tests)
            for test in tests:

                if test.get_owner() is None:
                    test.get_kwargs().update({"owner": suite_object.get_owner()})

                if not Settings.is_undefined(self.args):
                    if not is_relevant(_suite=suite, _test=test):
                        continue

                if test.accepts_suite_parameters() or test.accepts_test_parameters():
                    self.aggregated_data["parameterized_test_count"] += 1

                for context in [feature_context, suite_context]:
                    CliAudit.process_tags(context, test)
                    CliAudit.process_property(context, "components", test.get_component())
                    CliAudit.process_property(context, "owners", test.get_owner())

                self.update_context(suite, test, feature)

                module = "{}::{}".format(suite_object.get_class_module(), suite_object.get_class_name())
                if module not in self.aggregated_data["test_roster"]:
                    self.aggregated_data["test_roster"].update({module: {}})

                doc_html = None
                if test.get_function_object().__doc__:
                    from markdown2 import Markdown
                    markdowner = Markdown(extras=["tables"])  # TODO allow extras to be configured via config
                    doc = test.get_function_object().__doc__.replace("\n        ", "\n")
                    doc_html = markdowner.convert(doc)

                self.aggregated_data["test_roster"][module].update(
                    {test.get_function_name(): {"suite_name": suite_object.get_class_name(),
                                                "suite_module": suite_object.get_class_module(),
                                                "owner": test.get_owner(),
                                                "feature": suite_object.get_feature(),
                                                "component": test.get_component(),
                                                "tags": test.get_tags(),
                                                "doc": test.get_function_object().__doc__,
                                                "doc_html": doc_html,
                                                }})
            self.aggregated_data["context_by_suites"].update({suite_object.get_class_name(): suite_context})

    @staticmethod
    def process_property(data_context, prop, key):
        if key not in data_context[prop]:
            data_context[prop].update({key: 1})
        else:
            data_context[prop][key] += 1

    @staticmethod
    def process_tags(data_context, test):
        for tag in test.get_tags():
            if tag not in data_context["tags"]:
                data_context["tags"].update({tag: 1})
            else:
                data_context["tags"][tag] += 1

    def update_context(self, suite, test, feature):

        def process_data_context(_data_context, _context):

            if _context != "tags":
                CliAudit.process_tags(_data_context, test)
            if _context != "components":
                CliAudit.process_property(_data_context, "components", test.get_component())
            if _context != "owners":
                CliAudit.process_property(_data_context, "owners", test.get_owner())

            CliAudit.process_property(_data_context, "features", feature)
            CliAudit.process_property(_data_context, "suites", "{}.{}".format(suite.__module__, suite.__name__))

        def get_template(_context):
            template = {"total_tests": 0}
            for attribute in CliAudit.__SECTIONS:
                if attribute != _context:
                    template.update({attribute: {}})
            return template

        def update_context_template(_value, _context):

            if _value not in self.aggregated_data["context_by_{context}".format(context=context)]:
                self.aggregated_data["context_by_{context}".format(context=context)].update(
                    {_value: get_template(_context)})
            data_context = self.aggregated_data["context_by_{context}".format(context=context)][_value]
            data_context["total_tests"] += 1
            process_data_context(data_context, _context)

        for context in ["tags", "components", "owners"]:
            if context == "tags":
                for tag in test.get_tags():
                    update_context_template(tag, context)
            else:
                value = test.get_component() if context == "components" else test.get_owner()
                update_context_template(value, context)

    def print_results(self, command):

        from test_junkie.cli.utils import Color
        match_found = False
        output = []
        for data_context in CliAudit.__SECTIONS:
            if data_context == command:
                data = self.aggregated_data["context_by_{context}".format(context=data_context)]
                if data:
                    section = []
                    _sorted_data = sorted(data.items(), key=lambda x: x[1]["total_tests"])
                    _sorted_data.reverse()
                    _sorted_data = collections.OrderedDict(_sorted_data)
                    for primary_key, context in _sorted_data.items():
                        details = []
                        if data_context == "suites":
                            details.append("\nSuite: {value} Feature: {feature}"
                                           .format(value=Color.format_bold_string(primary_key),
                                                   feature=Color.format_bold_string(context["feature"])))
                        else:
                            parent = "".join(list(data_context)[:-1]).capitalize()  # exp: features > Feature
                            if primary_key is None:
                                primary_key = Color.format_string(primary_key, "red")
                            else:
                                primary_key = Color.format_bold_string(primary_key)
                            details.append("\n{parent}: {value}".format(parent=parent, value=primary_key))

                        from test_junkie.metrics import Aggregator
                        details.append("\t- Tests:\t{total} of {absolute} total tests ({percentage}%)"
                                       .format(total=context["total_tests"],
                                               absolute=self.aggregated_data["absolute_test_count"],
                                               percentage=Aggregator.percentage(
                                                   self.aggregated_data["absolute_test_count"],
                                                   context["total_tests"])))

                        for i in CliAudit.__SECTIONS:
                            if i in context:
                                msg = "\t"
                                counter = 0
                                _sorted_context = sorted(context[i].items(), key=lambda x: x[1])
                                _sorted_context.reverse()
                                _sorted_context = collections.OrderedDict(_sorted_context)
                                for key, count in _sorted_context.items():
                                    if counter > 0:
                                        msg += "\n\t\t\t"
                                    if key is None:
                                        key = Color.format_string(key, "red")
                                    msg += "{} ({})".format(key, count)
                                    counter += 1
                                if len(msg) > 0:
                                    details.append("\t- {i}: {msg}".format(i=i.capitalize(), msg=msg))
                        if len(details) >= 5:
                            section += details
                    if len(section) > 1:
                        output.append(section)
                    break

        for section in output:
            if len(section) >= 5:
                match_found = True
                for msg in section:
                    print(msg)

        if not match_found:
            print("[{status}] Nothing matches your search criteria!"
                  .format(status=Color.format_string("INFO", "blue")))
