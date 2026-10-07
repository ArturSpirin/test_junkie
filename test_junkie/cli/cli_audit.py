import collections

from test_junkie.builder import Builder
from test_junkie.constants import Undefined


class CliAudit:

    def __init__(self, suites, args, sources=None, scan_seconds=None):

        self.suites = suites
        self.exe_roster = Builder.get_execution_roster()
        self.args = args
        self.sources = sources
        self.scan_seconds = scan_seconds
        self.records = []  # one per audited test: what print_results() builds every view from
        self.scanned_tests = 0

    def __arg(self, name):
        value = getattr(self.args, name, Undefined)
        return None if value in (Undefined, None) else value

    def aggregate(self):

        def suite_relevant(_suite):
            from test_junkie.rules import Rules
            from test_junkie.listener import Listener
            args = self.args
            if (args.no_rules and _suite.get_rules().__class__ != Rules) or \
                    (args.no_listeners and _suite.get_listener().__class__ != Listener) or \
                    (args.no_suite_retries and _suite.get_retry_limit() > 1) or \
                    (args.no_suite_meta and _suite.get_meta()) or \
                    (args.no_owners and _suite.get_owner()) or (args.no_features and _suite.get_feature()):
                return False
            features = self.__arg("features")
            return features is None or _suite.get_feature() in features

        def test_relevant(_test):
            args = self.args
            if args.no_test_retries and _test.get_retry_limit() > 1:
                return False
            if args.no_test_meta:
                # the test's declared meta - get_meta() isn't used because it builds the per-parameter structure
                declared = _test.get_kwargs().get("meta") or {}
                if declared.get("original", declared):
                    return False
            if (args.no_owners and _test.get_owner()) or (args.no_components and _test.get_component()) or \
                    (args.no_tags and _test.get_tags()):
                return False
            owners, components = self.__arg("owners"), self.__arg("components")
            if owners is not None and _test.get_owner() not in owners:
                return False
            if components is not None and _test.get_component() not in components:
                return False
            tags = set(_test.get_tags())
            any_of, all_of = self.__arg("run_on_match_any"), self.__arg("run_on_match_all")
            if any_of is not None and not tags.intersection(any_of):
                return False
            return all_of is None or set(all_of).issubset(tags)

        # suites are listed by class name - unless two audited suites share it (same class name in different files),
        # then by module.ClassName. They used to be merged into one entry
        names = collections.Counter(suite.__name__ for suite in self.suites)
        for suite in self.suites:
            suite_object = self.exe_roster.get(suite, None)
            if suite_object is None:
                continue
            self.scanned_tests += len(suite_object.get_test_objects())
            if not suite_relevant(suite_object):
                continue
            suite_key = suite_object.get_class_name() if names[suite.__name__] == 1 else \
                "{}.{}".format(suite_object.get_class_module(), suite_object.get_class_name())
            for test in suite_object.get_test_objects():
                if test.get_owner() is None:
                    test.get_kwargs().update({"owner": suite_object.get_owner()})
                if test_relevant(test):
                    self.records.append({"suites": suite_key, "features": suite_object.get_feature(),
                                         "owners": test.get_owner(), "components": test.get_component(),
                                         "tags": list(test.get_tags()), "test": test.get_function_name()})

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
        for name, label in (("owners", "owners"), ("features", "features"), ("components", "components"),
                            ("run_on_match_any", "tags any"), ("run_on_match_all", "tags all")):
            value = self.__arg(name)
            if value is not None:
                filters.append("{} {}".format(label, ", ".join(str(item) for item in value)))
        if getattr(args, "suites", None):
            filters.append("suites {}".format(", ".join(args.suites)))
        return filters

    def __values(self, record, kind):
        value = record[kind]
        if kind == "tags":
            return value or [None]
        return [value]

    def __gaps(self):
        return dict((kind, sum(1 for record in self.records if None in self.__values(record, kind)))
                    for kind in ("owners", "components", "tags", "features"))

    def __json(self):
        import json
        view, total = self.args.command, len(self.records)
        blocks = collections.OrderedDict()
        for record in self.records:
            for key in self.__values(record, view):
                blocks.setdefault(key, []).append(record)
        out = {"view": view, "tests": total, "scanned_tests": self.scanned_tests, "filters": self.__filters(),
               "gaps": self.__gaps(), "blocks": []}
        for key, items in sorted(blocks.items(), key=lambda item: (item[0] is None, -len(item[1]), str(item[0]))):
            block = {"name": key, "tests": len(items), "share": round(100.0 * len(items) / total, 1) if total else 0}
            for kind in self.__ROWS[view]:
                block[kind] = dict(collections.Counter(
                    "none" if value is None else value for record in items for value in self.__values(record, kind)))
            block["test_names"] = ["{}.{}".format(r["suites"], r["test"]) for r in items]
            out["blocks"].append(block)
        print(json.dumps(out, indent=1))

    def __fail_on_gaps(self):
        wanted = getattr(self.args, "fail_on_gaps", None)
        if not wanted:
            return
        kinds = [kind.strip() for kind in wanted.split(",") if kind.strip()]
        unknown = [kind for kind in kinds if kind not in ("owners", "components", "tags", "features")]
        if unknown:
            from test_junkie.cli.cli import CliUtils
            CliUtils.error("--fail-on-gaps takes owners, features, components or tags, got: {}".format(
                ", ".join(unknown)), "e.g. tj audit suites --fail-on-gaps owners,tags")
        gaps = self.__gaps()
        found = ["{} test{} without {}".format(gaps[kind], "" if gaps[kind] == 1 else "s", kind[:-1] if
                 kind != "tags" else "tags") for kind in kinds if gaps[kind]]
        if found:
            if not self.args.json:
                from test_junkie.console import Console
                console = Console(None, mode="report")
                console.emit(["{}  {}".format(console.badge("FAILED", "err"), ", ".join(found)) +
                              console.style("  exit code 1", "dim")])
            exit(1)

    def print_results(self):
        if self.args.json:
            self.__json()
        else:
            self.__print()
        self.__fail_on_gaps()

    def __print(self):

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
