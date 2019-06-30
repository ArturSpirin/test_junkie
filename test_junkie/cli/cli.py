import argparse
import sys
import traceback
import pkg_resources

from test_junkie.cli.cli_aggregator import CliAggregator
from test_junkie.constants import DocumentationLinks
from test_junkie.errors import BadCliParameters
from test_junkie.settings import Settings
from colorama import Fore, Style


class Cli(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="",
            usage="""tj COMMAND

Modern Testing Framework

Commands:
run\t Run tests in any directory (recursive) 
audit\t Audit your tests in any directory (recursive) 
config\t Configure Test Junkie
version\t Display current version

Use: tj COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print("[{status}]\t\'{command}\' is not a test-junkie command\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red"), command=args.command))
            parser.print_help()
            exit(1)
        if args.command:
            getattr(self, args.command)()

    def run(self):
        parser = argparse.ArgumentParser(description='Run tests from command line',
                                         usage="tj run [OPTIONS]")

        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Test Junkie will only run suites provided, "
                                 "given that they are found in the SOURCE")

        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")

        CliUtils.add_standard_tj_args(parser)

        args = parser.parse_args(sys.argv[2:])

        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.cli_runner import RunnerManager
        try:
            tj = RunnerManager(sources=args.sources, ignore=[".git"], suites=args.suites)
            tj.scan()
        except BadCliParameters as error:
            print("[{status}] {error}".format(status=CliUtils.format_color_string("ERROR", "red"), error=error))
            return
        tj.run_suites(args)

    def audit(self):
        parser = argparse.ArgumentParser(usage="""tj audit [OPTIONS]

Scan and display aggregated and/or filtered test information
""")

        parser.add_argument("--by-tags", action="store_true", default=False,
                            help="Present aggregated data broken down by tags")

        parser.add_argument("--by-suites", action="store_true", default=False,
                            help="Present aggregated data broken down by suites")

        parser.add_argument("--by-owners", action="store_true", default=False,
                            help="Present aggregated data broken down by owners")

        parser.add_argument("--by-components", action="store_true", default=False,
                            help="Present aggregated data broken down by components")

        parser.add_argument("--by-features", action="store_true", default=False,
                            help="Present aggregated data broken down by features")

        parser.add_argument("--no-rules", action="store_true", default=False,
                            help="Aggregate data only for suites that do not have any rules set")

        parser.add_argument("--no-listeners", action="store_true", default=False,
                            help="Aggregate data only for suites that do not have any event listeners set")

        parser.add_argument("--no-suite-retries", action="store_true", default=False,
                            help="Aggregate data only for suites that do not have retries set")

        parser.add_argument("--no-test-retries", action="store_true", default=False,
                            help="Aggregate data only for tests that do not have retries set")

        parser.add_argument("--no-suite-meta", action="store_true", default=False,
                            help="Aggregate data only for suites that do not have any meta information set")

        parser.add_argument("--no-test-meta", action="store_true", default=False,
                            help="Aggregate data only for tests that do not have any meta information set")

        parser.add_argument("--no-owners", action="store_true", default=False,
                            help="Aggregate data only for tests that do not have any owners defined")

        parser.add_argument("--no-features", action="store_true", default=False,
                            help="Aggregate data only for suites that do not have features defined")

        parser.add_argument("--no-components", action="store_true", default=False,
                            help="Aggregate data only for tests that do not have any components defined")

        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Test Junkie will only run suites provided, "
                                 "given that they are found in the SOURCE")

        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")

        CliUtils.add_standard_tj_args(parser, audit=True)
        args = parser.parse_args(sys.argv[2:])

        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.cli_runner import RunnerManager
        try:
            tj = RunnerManager(sources=args.sources, ignore=[".git"], suites=args.suites)
            tj.scan()
        except BadCliParameters as error:
            print("[{status}] {error}".format(status=CliUtils.format_color_string("ERROR", "red"), error=error))
            return
        aggregator = CliAggregator(suites=tj.suites, args=args)
        aggregator.aggregate()
        aggregator.print_results()

    def config(self):
        parser = argparse.ArgumentParser(usage="""tj config COMMAND

Allows to configure Test Junkie the way you want it

Commands:
show\t Display current configuration for Test-Junkie
update\t Update configuration settings for individual properties via cli 
restore\t Will restore config to it\'s original values

Use: tj config COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', default=None, help="command to run")
        try:
            if len(sys.argv) >= 3:
                command = str(sys.argv[2:3][0])
                if command in ["show", "update", "restore"]:
                    from test_junkie.cli.cli_config import ConfigManager
                    return ConfigManager(command, sys.argv)
            parser.print_help()
        except:
            if "SystemExit:" not in traceback.format_exc():
                CliUtils.print_color_traceback()
                parser.print_help()
                exit(120)

    def version(self):
        print("Test Junkie {} (Python{})".format(pkg_resources.require("test-junkie")[0].version, sys.version_info[0]))


class CliUtils:

    def __init__(self):

        pass

    @staticmethod
    def add_standard_tj_args(parser, audit=False):
        """
        Generic parser args used to configure execution or set config settings
        """
        if not audit:
            parser.add_argument("-T", "--test_multithreading_limit", type=int, default=Settings.UNDEFINED,
                                help="Test level multi threading allows to run multiple tests concurrently.")

            parser.add_argument("-S", "--suite_multithreading_limit", type=int, default=Settings.UNDEFINED,
                                help="Suite level multi threading allows to run multiple suites concurrently.")

            parser.add_argument("-t", "--tests", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie can run specific tests. "
                                     "Provide the names of the tests that you want to execute/audit.")

        parser.add_argument("-f", "--features", nargs="+", default=Settings.UNDEFINED,
                            help="Test suites can be defined with a feature that they are testing. "
                                 "Use features to narrow down execution/audit of test suites only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.FEATURES))

        parser.add_argument("-c", "--components", nargs="+", default=Settings.UNDEFINED,
                            help="Tests can be defined with a component that they are testing. "
                                 "Use components to narrow down execution/audit of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.COMPONENTS))

        parser.add_argument("-o", "--owners", nargs="+", default=Settings.UNDEFINED,
                            help="Tests & test suites can be defined with an assignee. "
                                 "Use owners to narrow down execution/audit of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.ASSIGNEES))

        if not audit:
            parser.add_argument("-m", "--monitor_resources", action="store_true", default=Settings.UNDEFINED,
                                help="Test Junkie can track resource usage for CPU & Memory as it runs tests")

            parser.add_argument("--html_report", type=str, default=Settings.UNDEFINED,
                                help="Path to FILE. This will enable HTML report generation and when ready, "
                                     "the report will be saved to the specified file")

            parser.add_argument("--xml_report", type=str, default=Settings.UNDEFINED,
                                help="Path to FILE. This will enable XML report generation and when ready, "
                                     "the report will be saved to the specified file")

            parser.add_argument("-l", "--run_on_match_all", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie will RUN tests that match ALL of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-k", "--run_on_match_any", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie will RUN tests that match ANY of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-j", "--skip_on_match_all", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie will SKIP tests that match ALL of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-g", "--skip_on_match_any", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie will SKIP tests that match ANY of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))
        else:
            parser.add_argument("-l", "--tags", nargs="+", default=Settings.UNDEFINED,
                                help="Test Junkie will audit tests that match those tags.")

        parser.add_argument("-s", "--sources", nargs="+", default=Settings.UNDEFINED,
                            help="Paths to DIRECTORY or FILE where you have your tests. "
                                 "Test Junkie will traverse this source(s) looking for test suites")

    @staticmethod
    def add_standard_boolean_tj_args(parser):
        """
        Generic parser args used to show and restore config settings
        """

        parser.add_argument("-s", "--sources", action="store_true", default=False,
                            help="Paths to DIRECTORY or FILE where you have your tests. "
                                 "Test Junkie will traverse this source(s) looking for test suites")

        parser.add_argument("-T", "--test_multithreading_limit", action="store_true", default=False,
                            help="Test level multi threading allows to run multiple tests concurrently.")

        parser.add_argument("-S", "--suite_multithreading_limit", action="store_true", default=False,
                            help="Suite level multi threading allows to run multiple suites concurrently.")

        parser.add_argument("-t", "--tests", nargs="+", default=Settings.UNDEFINED,
                            help="Test Junkie can run specific tests. "
                                 "Provide the names of the tests that you want to run.")

        parser.add_argument("-f", "--features", action="store_true", default=False,
                            help="Test suites can be defined with a feature that they are testing. "
                                 "Use features to narrow down execution of test suites only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.FEATURES))

        parser.add_argument("-c", "--components", action="store_true", default=False,
                            help="Tests can be defined with a component that they are testing. "
                                 "Use components to narrow down execution of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.COMPONENTS))

        parser.add_argument("-o", "--owners", action="store_true", default=False,
                            help="Tests & test suites can be defined with an assignee. "
                                 "Use owners to narrow down execution of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.ASSIGNEES))

        parser.add_argument("-m", "--monitor_resources", action="store_true", default=False,
                            help="Test Junkie can track resource usage for CPU & Memory as it runs tests")

        parser.add_argument("--html_report", action="store_true", default=False,
                            help="Path to FILE. This will enable HTML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("--xml_report", action="store_true", default=False,
                            help="Path to FILE. This will enable XML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("-l", "--run_on_match_all", action="store_true", default=False,
                            help="Test Junkie will RUN tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-k", "--run_on_match_any", action="store_true", default=False,
                            help="Test Junkie will RUN tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-j", "--skip_on_match_all", action="store_true", default=False,
                            help="Test Junkie will SKIP tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-g", "--skip_on_match_any", action="store_true", default=False,
                            help="Test Junkie will SKIP tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

    @staticmethod
    def format_color_string(value, color):
        colors = {"red": Fore.RED, "green": Fore.GREEN, "yellow": Fore.YELLOW, "blue": Fore.BLUE}
        return "{style}{color}{value}{reset}".format(style=Style.BRIGHT, color=colors[color],
                                                     value=value, reset=Style.RESET_ALL)

    @staticmethod
    def print_color_traceback():
        print(Style.BRIGHT + Fore.RED)
        print(traceback.format_exc())
        print(Style.RESET_ALL)


if "__main__" == __name__:

    Cli()
