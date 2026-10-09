import argparse
import os
import sys
import traceback

from test_junkie.cli.cli_audit import CliAudit
from test_junkie.constants import DocumentationLinks, CliConstants, Undefined
from colorama import Fore, Style

# Every option the commands share, defined once: (setting, short flag, documented long flag, old spellings that
# still work, kind, help, where). kind: "list" (one or more values), "int", "seconds" (0 or more, decimals ok),
# "count" (0 or more), "truncate" (top, bottom or middle), "str" or "flag". where: "run" for tj run
# and tj config update/show/restore, "audit" for tj audit too, "once" for tj run only (not saved to the config)
_OPTIONS = [
    ("sources", "-s", "--sources", (), "list",
     "Directories or files with your tests. Test Junkie scans them for suites", "audit"),
    ("test_multithreading_limit", "-T", "--test-multithreading-limit", ("--test_multithreading_limit",), "int",
     "How many tests run at the same time", "run"),
    ("suite_multithreading_limit", "-S", "--suite-multithreading-limit", ("--suite_multithreading_limit",), "int",
     "How many suites run at the same time", "run"),
    ("tests", "-t", "--tests", (), "list",
     "Only these tests: names, Suite.test names or patterns like login_*", "run"),
    ("features", "-f", "--features", (), "list",
     "Only suites with these features. See " + DocumentationLinks.FEATURES, "audit"),
    ("components", "-c", "--components", (), "list",
     "Only tests with these components. See " + DocumentationLinks.COMPONENTS, "audit"),
    ("owners", "-o", "--owners", (), "list",
     "Only tests with these owners. See " + DocumentationLinks.ASSIGNEES, "audit"),
    ("run_on_match_all", "-l", "--tags-all", ("--run-on-match-all", "--run_on_match_all"), "list",
     "Only tests that have ALL of these tags. See " + DocumentationLinks.TAGS, "audit"),
    ("run_on_match_any", "-k", "--tags-any", ("--run-on-match-any", "--run_on_match_any"), "list",
     "Only tests that have ANY of these tags", "audit"),
    ("skip_on_match_all", "-j", "--skip-tags-all", ("--skip-on-match-all", "--skip_on_match_all"), "list",
     "Skip tests that have ALL of these tags", "run"),
    ("skip_on_match_any", "-g", "--skip-tags-any", ("--skip-on-match-any", "--skip_on_match_any"), "list",
     "Skip tests that have ANY of these tags", "run"),
    ("retry", None, "--retry", (), "int",
     "Run each failing test up to this many times, whatever its @test(retry=) says", "run"),
    ("no_retry", None, "--no-retry", ("--no_retry",), "flag", "Run every test and suite once, no retries", "run"),
    ("suite_throttling", None, "--suite-throttling", (), "seconds",
     "At least this many seconds between two suites starting, across the run. See " + DocumentationLinks.THROTTLING,
     "run"),
    ("test_throttling", None, "--test-throttling", (), "seconds",
     "At least this many seconds between two tests starting, across the run", "run"),
    ("ramp_up", None, "--ramp-up", (), "seconds",
     "Grow the suite and test thread limits from 1 to -S/-T over this many seconds", "run"),
    ("rerun", None, "--rerun", (), "str",
     "Run again only what didn't pass in this JSON report (--json-report), down to the parameter", "once"),
    ("seed", None, "--seed", (), "int",
     "Seed for TestOrder.RANDOM, to repeat an order (the header prints the one used)", "once"),
    ("monitor_resources", "-m", "--monitor-resources", ("--monitor_resources",), "flag",
     "Track CPU and memory, and chart them after the summary", "run"),
    ("html_report", None, "--html-report", ("--html_report",), "str",
     "Write an HTML report to this file, or to report.html in this folder", "run"),
    ("xml_report", None, "--xml-report", ("--xml_report",), "str",
     "Write a JUnit XML report to this file, or to report.xml in this folder", "run"),
    ("json_report", None, "--json-report", ("--json_report",), "str",
     "Write a JSON report to this file, or to report.json in this folder", "run"),
    ("traceback_limit", None, "--traceback-limit", (), "count",
     "Keep at most this many characters of each traceback. See " + DocumentationLinks.TRUNCATION, "run"),
    ("message_limit", None, "--message-limit", (), "count",
     "Keep at most this many characters of each exception message", "run"),
    ("truncate", None, "--truncate", (), "truncate",
     "What to keep of a message or traceback over its limit: top cuts the start, bottom cuts the end, "
     "middle keeps both ends (default)", "run"),
    ("quiet", "-q", "--quiet", (), "flag", "Only print the problems and the result line", "run"),
    ("per_test", "-p", "--per-test", ("--per_test",), "flag",
     "Print one line per test instead of a progress bar per suite", "run"),
    ("no_capture", None, "--no-capture", ("--no_capture",), "flag",
     "Show what tests print and log as it happens. Needed for breakpoint() / pdb", "run"),
    ("code_cov", None, "--code-cov", ("--code_cov",), "flag", "Measure code coverage", "run"),
    ("cov_rcfile", None, "--cov-rcfile", ("--cov_rcfile",), "str",
     "Configuration file for coverage.py. See " + DocumentationLinks.COVERAGE_CONFIG_FILE, "run"),
    ("guess_root", None, "--guess-root", ("--guess_root",), "flag",
     "If an import fails, look for your project's root in the folders above the test files", "audit"),
]
def _at_least_zero(convert, what):
    def parse(value):
        try:
            number = convert(value)
        except ValueError:
            number = -1
        if number < 0:
            raise argparse.ArgumentTypeError("needs {}, got {!r}".format(what, value))
        return number
    parse.__name__ = what  # argparse names the type in its error
    return parse


def _seconds(value):
    number = _at_least_zero(float, "0 or more seconds")(value)
    return int(number) if number == int(number) else number  # saved as 2, not 2.0


_KINDS = {"list": {"nargs": "+"}, "int": {"type": int}, "str": {"type": str}, "flag": {"action": "store_true"},
          "seconds": {"type": _seconds}, "count": {"type": _at_least_zero(int, "a whole number of 0 or more")},
          "truncate": {"type": str, "choices": ("top", "bottom", "middle")}}
_METAVARS = {"sources": "PATH", "tests": "TEST", "features": "FEATURE", "components": "COMPONENT", "owners": "OWNER",
             "run_on_match_all": "TAG", "run_on_match_any": "TAG", "skip_on_match_all": "TAG",
             "skip_on_match_any": "TAG", "html_report": "FILE", "xml_report": "FILE", "json_report": "FILE",
             "rerun": "FILE", "cov_rcfile": "FILE", "suite_throttling": "SECONDS", "test_throttling": "SECONDS",
             "ramp_up": "SECONDS", "traceback_limit": "CHARS", "message_limit": "CHARS",
             "truncate": "{top,bottom,middle}"}
_AUDIT_VIEWS = ["suites", "features", "components", "tags", "owners", "conflicts"]


def _add(parser, dest, short, long_flag, aliases, extra, help_text):
    parser.add_argument(*([short, long_flag] if short else [long_flag]), dest=dest, help=help_text, **extra)
    if aliases:  # old spellings keep working without crowding -h
        parser.add_argument(*aliases, dest=dest, help=argparse.SUPPRESS,
                            **dict(extra, default=argparse.SUPPRESS))


class Cli(object):

    def __init__(self):
        parser = argparse.ArgumentParser(prog="tj", usage="""tj COMMAND

Commands:
run\t Run tests from a directory or file
audit\t Report on your tests' owners, features, components and tags without running them
config\t Save settings for tj run and tj audit
version\t Show the version, Python, install and config locations

Use: tj COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        if len(sys.argv) < 2:
            CliUtils.error("Which command? e.g. tj run -s tests, or tj audit suites -s tests",
                           "Commands: run, audit, config, version. tj -h explains each one.")
        args = parser.parse_args(sys.argv[1:2])
        if args.command.startswith("_") or not hasattr(self, args.command):
            CliUtils.error("'{}' is not a test-junkie command. Use one of: run, audit, config, version"
                           .format(args.command), "tj -h explains each one.")
        getattr(self, args.command)()

    def run(self):
        parser = argparse.ArgumentParser(description='Run tests from command line', usage="tj run [OPTIONS]")
        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Only these suites: names or patterns like Login*")
        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")
        parser.add_argument("--config", type=str, default=Undefined,
                            help="Settings file to use instead of the project's tj.cfg or your user config")
        CliUtils.add_options(parser, "run")

        args = parser.parse_args(sys.argv[2:])

        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.cli_runner import CliRunner
        # scan() reports bad parameters (e.g. no sources) itself and exits 120
        tj = CliRunner(sources=args.sources, ignore=[".git"], suites=args.suites,
                       code_cov=args.code_cov, cov_rcfile=args.cov_rcfile, guess_root=args.guess_root,
                       config=args.config)
        tj.scan()
        tj.run_suites(args)

    def audit(self):
        parser = argparse.ArgumentParser(description='Scan and display aggregated and/or filtered test information',
                                         usage="""tj audit VIEW [OPTIONS]

Report on your tests without running them. Views:
suites\t\t one block per suite
features\t one block per feature
components\t one block per component
tags\t\t one block per tag
owners\t\t one block per owner
conflicts\t every pair of tests that must not run together (conflicts_with=)
""")
        parser.add_argument('command', help='the view: suites, features, components, tags, owners or conflicts')
        for flag, text in (("--by-components", "Split every block by component"),
                           ("--by-features", "Split every block by feature"),
                           ("--no-rules", "Only suites without custom rules"),
                           ("--no-listeners", "Only suites without custom event listeners"),
                           ("--no-suite-retries", "Only suites without retries"),
                           ("--no-test-retries", "Only tests without retries"),
                           ("--no-suite-meta", "Only suites without meta"),
                           ("--no-test-meta", "Only tests without meta"),
                           ("--no-owners", "Only tests without an owner"),
                           ("--no-features", "Only suites without a feature"),
                           ("--no-components", "Only tests without a component"),
                           ("--no-tags", "Only tests without tags")):
            parser.add_argument(flag, action="store_true", default=False, help=text)
        parser.add_argument("--json", action="store_true", default=False,
                            help="Print the result as JSON, for scripts and CI")
        parser.add_argument("--fail-on-gaps", nargs="?", const="owners,features,components,tags", default=None,
                            metavar="KINDS", help="Exit 1 if any test has no owner, feature, component or tag "
                                                  "(or just the kinds listed, e.g. owners,tags)")
        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Only these suites: names or patterns like Login*")
        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")
        parser.add_argument("--config", type=str, default=Undefined,
                            help="Settings file to use instead of the project's tj.cfg or your user config")
        CliUtils.add_options(parser, "audit")
        # tj audit --tags was the only tag filter (any of the tags); it's tj run's --tags-any now
        parser.add_argument("--tags", nargs="+", dest="run_on_match_any", help=argparse.SUPPRESS,
                            default=argparse.SUPPRESS)

        if len(sys.argv) < 3:
            CliUtils.error("Which view? e.g. tj audit suites, or tj audit owners --no-owners",
                           "Views: suites, features, components, tags, owners. tj audit -h lists every option.")
        args = parser.parse_args(sys.argv[2:])
        if args.command not in _AUDIT_VIEWS:
            CliUtils.error("'{}' is not an audit view. Use one of: suites, features, components, tags, owners, "
                           "conflicts"
                           .format(args.command), "tj audit -h lists every option.")
        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.cli_runner import CliRunner
        tj = CliRunner(sources=args.sources, ignore=[".git"], suites=args.suites, guess_root=args.guess_root,
                       config=args.config, quiet_scan=args.json)
        tj.scan()
        aggregator = CliAudit(suites=tj.suites, args=args, sources=tj.sources, scan_seconds=tj.scan_seconds)
        aggregator.aggregate()
        aggregator.print_results()

    def config(self):
        parser = argparse.ArgumentParser(usage="""tj config COMMAND [--config FILE]

Save settings for tj run and tj audit. Without --config it uses the project's tj.cfg (in the working directory)
if there is one, otherwise your user config.

Commands:
show\t Show settings (--all for every one)
update\t Save settings, e.g. tj config update -s tests -T 4
restore\t Clear settings back to their defaults (--all for every one)
""")
        parser.add_argument('command', default=None, help="command to run")
        argv = list(sys.argv)
        config = None
        if "--config" in argv:
            index = argv.index("--config")
            if index + 1 >= len(argv):
                CliUtils.error("--config needs a file, e.g. tj config show --all --config ./tj.cfg",
                               "Nothing was changed.")
            config = argv[index + 1]
            del argv[index:index + 2]
        try:
            if len(argv) >= 3:
                command = str(argv[2])
                if command in ["show", "update", "restore"]:
                    from test_junkie.cli.cli_config import CliConfig, Config
                    return CliConfig(config or Config.project_path() or CliConstants.TJ_CONFIG_NAME, command, argv,
                                     create=config is not None and command == "update")
                elif command not in ["-h", "--help"]:
                    CliUtils.error("'{}' is not a config command. Use one of: show, update, restore".format(command),
                                   "tj config -h explains each one.")
            else:
                CliUtils.error("Which config command? e.g. tj config show --all, or tj config update -s tests",
                               "Commands: show, update, restore. tj config -h explains each one.")
            parser.print_help()
        except SystemExit:
            raise  # was swallowed here, so a failed `tj config update` exited 0
        except Exception:
            CliUtils.print_color_traceback()
            parser.print_help()
            exit(120)

    def version(self):
        import test_junkie
        from test_junkie.console import Console
        from test_junkie.cli.cli_config import Config
        console = Console(None, mode="report")
        project = Config.project_path()
        config = project or Config.get_config_path(CliConstants.TJ_CONFIG_NAME)
        rows = [("package", os.path.dirname(os.path.abspath(test_junkie.__file__))),
                ("config", config + ("" if project else console.style("  (user config)", "dim"))),
                ("docs", DocumentationLinks.DOMAIN)]
        console.emit(console.head(rows)[:-1])


class CliUtils:

    __INITIALIZED = False

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @staticmethod
    def add_options(parser, command):
        """
        :param command: "run" (tj run, tj config update), "audit" (tj audit) or "toggle" (tj config show/restore:
                        every saved setting as an on/off switch)
        """
        for dest, short, long_flag, aliases, kind, help_text, where in _OPTIONS:
            if command == "audit" and where != "audit":
                continue
            if command == "toggle":
                if where == "once":
                    continue
                extra = {"action": "store_true", "default": False}
            else:
                if command == "update" and where == "once":
                    continue
                extra = dict(_KINDS[kind], default=Undefined)
                if kind != "flag":
                    extra["metavar"] = _METAVARS.get(dest, "N")
            _add(parser, dest, short, long_flag, aliases, extra, help_text)

    @staticmethod
    def add_standard_tj_args(parser, audit=False):
        CliUtils.add_options(parser, "audit" if audit else "update")

    @staticmethod
    def add_standard_boolean_tj_args(parser):
        CliUtils.add_options(parser, "toggle")

    @staticmethod
    def __initialize():
        if not CliUtils.__INITIALIZED:
            import colorama
            colorama.init()
            CliUtils.__INITIALIZED = True

    @staticmethod
    def format_color_string(value, color):
        CliUtils.__initialize()
        colors = {"red": Fore.RED, "green": Fore.GREEN, "yellow": Fore.YELLOW, "blue": Fore.BLUE}
        return "{style}{color}{value}{reset}".format(style=Style.BRIGHT, color=colors[color],
                                                     value=value, reset=Style.RESET_ALL)

    @staticmethod
    def print_color_traceback(trace=None):
        CliUtils.__initialize()
        print(Style.BRIGHT + Fore.RED)
        if trace is None:
            print(traceback.format_exc())
        else:
            print(trace)
        print(Style.RESET_ALL)

    @staticmethod
    def error(message, hint, code=120):
        """
        Prints an ERROR line with what to do instead, the way tj run, audit and config report errors, then exits
        """
        from test_junkie.console import Console
        console = Console(None, mode="report")
        console.emit(["{}  {}".format(console.badge("ERROR", "err"), message), "         " + console.style(hint, "dim")])
        exit(code)

    @staticmethod
    def format_bold_string(value):
        CliUtils.__initialize()
        return "{bold}{value}{end}".format(bold=CliUtils.BOLD, value=value, end=CliUtils.END)


if "__main__" == __name__:

    Cli()
