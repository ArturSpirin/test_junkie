import collections

from test_junkie.builder import Builder
from test_junkie.constants import Undefined


class CliAudit:

    __SECTIONS = ["owners", "features", "suites", "components", "tags"]

    def __init__(self, suites, args, sources=None, scan_seconds=None):

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
        self.sources = sources
        self.scan_seconds = scan_seconds
        self.records = []  # one per audited test: what print_results() builds every view from
        self.scanned_tests = 0

    def aggregate(self):

        def is_relevant(_suite, _test=None):
            if not _test:
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

                if self.args.no_features and _suite.get_feature():
                    return False

                if self.args.features != Undefined:
                    if _suite.get_feature() in self.args.features:
                        return True
                    return False
            else:
                if self.args.no_test_retries and _test.get_retry_limit() > 1:
                    return False

                if self.args.no_test_meta:
                    # the test's declared meta - this used to check the *suite's* meta. get_meta() isn't used
                    # because it builds the per-parameter structure as a side effect
                    declared = _test.get_kwargs().get("meta") or {}
                    if declared.get("original", declared):
                        return False

                if self.args.no_owners and _test.get_owner():
                    return False

                if self.args.no_components and _test.get_component():
                    return False

                if self.args.no_tags and _test.get_tags():
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

        # the suites that were scanned / asked for with -x - this used to walk every suite registered in the
        # process, so -x was ignored and a long-lived process audited everything it had ever loaded
        # suites are listed by class name - unless two audited suites share it (same class name in different files),
        # then by module.ClassName. They used to be merged into one entry
        names = collections.Counter(suite.__name__ for suite in self.suites)

        for suite in self.suites:
            suite_object = self.exe_roster.get(suite, None)
            if suite_object is not None:
                self.scanned_tests += len(suite_object.get_test_objects())
            if suite_object is None or not is_relevant(_suite=suite_object):
                continue

            all_tests = suite_object.get_test_objects()
            self.aggregated_data["absolute_test_count"] += len(all_tests)
            tests = []
            for test in all_tests:
                if test.get_owner() is None:
                    test.get_kwargs().update({"owner": suite_object.get_owner()})
                # test-level filters apply *before* counting - filtered-out tests used to still be counted
                if is_relevant(_suite=suite_object, _test=test):
                    tests.append(test)
            if not tests:
                continue
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

            for test in tests:
                if test.accepts_suite_parameters() or test.accepts_test_parameters():
                    self.aggregated_data["parameterized_test_count"] += 1

                for context in [feature_context, suite_context]:
                    CliAudit.process_tags(context, test)
                    CliAudit.process_property(context, "components", test.get_component())
                    CliAudit.process_property(context, "owners", test.get_owner())

                self.update_context(suite, test, feature)
            suite_key = suite_object.get_class_name() if names[suite.__name__] == 1 else \
                "{}.{}".format(suite_object.get_class_module(), suite_object.get_class_name())
            self.aggregated_data["context_by_suites"].update({suite_key: suite_context})
            for test in tests:
                self.records.append({"suites": suite_key, "features": feature, "owners": test.get_owner(),
                                     "components": test.get_component(), "tags": list(test.get_tags()),
                                     "test": test.get_function_name()})

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

    # what each view's blocks list under the block's name
    __ROWS = {"suites": ["features", "owners", "components", "tags"],
              "owners": ["suites", "features", "components", "tags"],
              "features": ["suites", "owners", "components", "tags"],
              "components": ["suites", "features", "owners", "tags"],
              "tags": ["suites", "features", "owners", "components"]}
    __SINGULAR = {"suites": "suite", "features": "feature", "owners": "owner", "components": "component", "tags": "tag"}
    __FLAGS = {"owners": "--no-owners", "features": "--no-features", "components": "--no-components",
               "tags": "--no-tags"}

    def __filters(self):
        """
        :return: LIST of the filters this audit ran with, as the header shows them
        """
        args, filters = self.args, []
        for flag, label in (("no_owners", "no owner"), ("no_features", "no feature"), ("no_components", "no component"),
                            ("no_tags", "no tags"), ("no_rules", "no rules"), ("no_listeners", "no listener"),
                            ("no_suite_retries", "no suite retries"), ("no_test_retries", "no test retries"),
                            ("no_suite_meta", "no suite meta"), ("no_test_meta", "no test meta")):
            if getattr(args, flag, False):
                filters.append(label)
        for name in ("owners", "features", "components", "tags"):
            value = getattr(args, name, Undefined)
            if value not in (Undefined, None):
                filters.append("{} {}".format(name, ", ".join(str(item) for item in value)))
        if getattr(args, "suites", None):
            filters.append("suites {}".format(", ".join(args.suites)))
        return filters

    def print_results(self):

        from test_junkie.console import Console
        console = Console(None, mode="report")
        style = console.style
        dot = style(" · ", "dim")
        view = self.args.command
        records = self.records
        total = len(records)
        filters = self.__filters()
        rows = [("tests", console.found(self.sources, len(set(r["suites"] for r in records)) if records else
                                        len(self.suites), total if records else self.scanned_tests,
                                        self.scan_seconds)),
                ("audit", view + (dot + "by features" if self.args.by_features else "") +
                 (dot + "by components" if self.args.by_components else ""))]
        if filters:
            rows.append(("filters", dot.join(filters)))
        lines = console.head(rows)

        if not records:
            lines.append("{} {}".format(style("Nothing matches.", "skip"), "{} test{} scanned{}.".format(
                self.scanned_tests, " was" if self.scanned_tests == 1 else "s were",
                ", none of them matches: " + ", ".join(filters) if filters else "")))
            console.emit(lines)
            return

        def values(record, kind):
            value = record[kind]
            if kind == "tags":
                return value or [None]
            return [value]

        def counted(items, kind):
            counts = collections.Counter(value for record in items for value in values(record, kind))
            ordered = sorted(counts.items(), key=lambda item: (item[0] is None, -item[1], str(item[0])))
            return dot.join("{} {}".format(style("none", "ign") if key is None else key, n) for key, n in ordered)

        def bar(n, missing):
            width = 16
            filled = int(round(width * n / float(total)))
            return "[{}{}]".format(style("|" * filled, "ign" if missing else "pass") if filled else "",
                                   style("·" * (width - filled), "dim"))

        blocks = collections.OrderedDict()
        for record in records:
            for key in values(record, view):
                blocks.setdefault(key, []).append(record)
        ordered = sorted(blocks.items(), key=lambda item: (item[0] is None, -len(item[1]), str(item[0])))
        listing = bool(filters)  # with a filter the point is finding the tests, so list them
        for key, items in ordered:
            name = "no {}".format(self.__SINGULAR[view] if view != "tags" else "tags") if key is None else str(key)
            title = style(name, "ign" if key is None else "bold")
            share = "{}%".format(int(round(100.0 * len(items) / total)))
            lines.append("{}{}{} test{}{}{}  {}".format(title, " " * max(2, 34 - len(name)), str(len(items)).rjust(3),
                                                       "" if len(items) == 1 else "s", dot, share.rjust(4),
                                                       bar(len(items), key is None)))
            for kind in self.__ROWS[view]:
                if (kind == "features" and self.args.by_features) or (kind == "components" and self.args.by_components):
                    continue  # the breakdown below lists them
                if view == "suites" and kind == "features":
                    feature = items[0]["features"]
                    lines.append("  {} {}".format(style("feature".ljust(12), "dim"),
                                                  style("none", "ign") if feature is None else feature))
                    continue
                lines.append("  {} {}".format(style(kind.ljust(12), "dim"), counted(items, kind)))
            for by, enabled in (("features", self.args.by_features), ("components", self.args.by_components)):
                if not enabled or by == view:
                    continue
                groups = collections.OrderedDict()
                for record in items:
                    for value in values(record, by):
                        groups.setdefault(value, []).append(record)
                for value, group in sorted(groups.items(), key=lambda item: (item[0] is None, -len(item[1]))):
                    label = style("none", "ign") if value is None else value
                    lines.append("  {} {} {}".format(style(self.__SINGULAR[by].ljust(12), "dim"), label, len(group)))
                    extra = [kind for kind in ("owners", "tags") if kind != view]
                    lines.append("  {} {}".format(" " * 12, "   ".join(
                        "{} {}".format(style(kind, "dim"), counted(group, kind)) for kind in extra)))
            if listing:
                names = ["{}.{}".format(r["suites"], r["test"]) if view != "suites" else r["test"] for r in items]
                shown = dot.join(names[:10]) + (style(" … and {} more".format(len(names) - 10), "dim")
                                                 if len(names) > 10 else "")
                lines.append("  {} {}".format(style("tests".ljust(12), "dim"), shown))
            lines.append("")

        gaps = []
        for kind in ("owners", "components", "tags", "features"):
            missing = sum(1 for record in records if None in values(record, kind))
            if missing and not getattr(self.args, "no_" + kind, False):
                what = {"owners": "no owner", "components": "no component", "tags": "no tags",
                        "features": "no feature"}[kind]
                gaps.append("  {} {} {}{}".format(
                    style("{} test{}".format(missing, "" if missing == 1 else "s").ljust(8), "ign"),
                    ("has" if missing == 1 else "have").ljust(4), what.ljust(17),
                    style("tj audit {} {}".format(view, self.__FLAGS[kind]), "dim")))
        if gaps:
            lines.extend([console.rule("Gaps", str(len(gaps))), ""] + gaps + [""])
        lines.append(style("─" * 80, "dim"))
        lines.append("")
        summary = ["{} test{}".format(total, "" if total == 1 else "s")]
        for kind in ("suites", "features", "owners", "components", "tags"):
            distinct = set(value for record in records for value in values(record, kind) if value is not None)
            summary.append("{} {}".format(len(distinct), kind if len(distinct) != 1 else self.__SINGULAR[kind]))
        lines.append(dot.join(summary))
        console.emit(lines)
