from test_junkie.builder import Builder
from test_junkie.constants import Undefined


class CliAggregator:

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

                "parameterized_test_count": 0,
                "parameterized_suite_count": 0,
                }
        self.suites = suites
        self.exe_roster = Builder.get_execution_roster()
        self.args = args

    def aggregate(self):

        def is_relevant(_suite=None, _test=None):
            if not _suite and not _test:
                raise Exception("Must pass in either a SuiteObject or a TestObject!")
            elif _suite and not _test:
                from test_junkie.rules import Rules
                if self.args.no_rules and _suite.get_rules().__class__ != Rules:
                    return False

                from test_junkie.listener import Listener
                if self.args.no_listeners and _suite.get_listener().__class__ != Listener:
                    return False

                if self.args.no_suite_retries and _suite.get_retry_limit() > 1:
                    return False

                if self.args.no_suite_meta and _suite.get_meta():
                    return False

                if self.args.no_owners and _suite.get_owner():
                    return False

                if self.args.features != Undefined:
                    if _suite.get_feature() in self.args.features:
                        return True
                    return False
            else:
                if self.args.no_test_retries and _test.get_retry_limit() > 1:
                    return False

                if self.args.no_test_meta and _suite.get_meta():
                    return False

                if self.args.no_owners and _test.get_owner():
                    return False
                if self.args.owners != Undefined:
                    if _test.get_owner() in self.args.owners:
                        return True
                    return False

                if self.args.components != Undefined:
                    if _test.get_component() in self.args.components:
                        return True
                    return False

                if self.args.tags != Undefined:
                    for tag in self.args.tags:
                        if tag in _test.get_tags():
                            return True
                    return False
            return True

        for suite, suite_object in self.exe_roster.items():
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
            feature_context["suites"].update({suite_object.get_class_name(): len(tests)})

            suite_context = {"total_tests": len(tests),
                             "tags": {},
                             "owners": {},
                             "components": {},
                             "feature": feature}

            self.aggregated_data["absolute_test_count"] += len(tests)
            for test in tests:

                if test.get_owner() is None:
                    test.get_kwargs().update({"owner": suite_object.get_owner()})

                if not is_relevant(_suite=suite, _test=test):
                    continue
                # self.aggregated_data["absolute_test_count"] += 1
                if test.accepts_suite_parameters() or test.accepts_test_parameters():
                    self.aggregated_data["parameterized_test_count"] += 1

                for context in [feature_context, suite_context]:
                    CliAggregator.process_tags(context, test)
                    CliAggregator.process_property(context, "components", test.get_component())
                    CliAggregator.process_property(context, "owners", test.get_owner())

                self.update_context(suite, test, feature)
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
                CliAggregator.process_tags(_data_context, test)
            if _context != "components":
                CliAggregator.process_property(_data_context, "components", test.get_component())
            if _context != "owners":
                CliAggregator.process_property(_data_context, "owners", test.get_owner())

            CliAggregator.process_property(_data_context, "features", feature)
            CliAggregator.process_property(_data_context, "suites", suite.__name__)

        def get_template(_context):
            template = {"total_tests": 0}
            for attribute in CliAggregator.__SECTIONS:
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

    def print_results(self):

        def requested(_data_context):

            _all = True
            for arg in CliAggregator.__SECTIONS:
                if getattr(self.args, "by_{}".format(arg)):
                    _all = False
            if not _all:
                return getattr(self.args, "by_{}".format(_data_context))
            return True

        from test_junkie.cli.cli import CliUtils
        match_found = False
        output = []
        for data_context in CliAggregator.__SECTIONS:
            if not requested(data_context):
                continue
            data = self.aggregated_data["context_by_{context}".format(context=data_context)]
            if data:
                section = ["\n[{status}] =============== AGGREGATION by {type} ==============="
                           .format(status=CliUtils.format_color_string("INFO", "blue"),
                                   type=data_context.upper())]
                for primary_key, context in data.items():
                    details = []
                    if data_context == "suites":
                        details.append("Suite: {value} Feature: {feature}"
                                          .format(value=primary_key, feature=context["feature"]))
                    elif data_context == "features":
                        details.append("Feature: {value}".format(value=primary_key))
                    elif data_context == "owners":
                        details.append("Owner: {value}".format(value=primary_key))
                    elif data_context == "components":
                        details.append("Component: {value}".format(value=primary_key))
                    elif data_context == "tags":
                        details.append("Tag: {value}".format(value=primary_key))

                    from test_junkie.metrics import Aggregator
                    details.append("\t- Tests: {total} of {absolute} total tests ({percentage}%)"
                                      .format(total=context["total_tests"],
                                              absolute=self.aggregated_data["absolute_test_count"],
                                              percentage=Aggregator.percentage(
                                                  self.aggregated_data["absolute_test_count"], context["total_tests"])))

                    for i in CliAggregator.__SECTIONS:
                        if i in context:
                            msg = ""
                            for key, count in context[i].items():
                                msg += "{}({}) ".format(key, count)
                            if len(msg) > 0:
                                details.append("\t- {i}: {msg}".format(i=i.capitalize(), msg=msg))
                    if len(details) >= 5:
                        section += details
                if len(section) > 1:
                    output.append(section)

        for section in output:
            if len(section) >= 5:
                match_found = True
                for msg in section:
                    print(msg)

        if not match_found:
            print("[{status}] Nothing matches your search criteria!"
                  .format(status=CliUtils.format_color_string("INFO", "blue")))
