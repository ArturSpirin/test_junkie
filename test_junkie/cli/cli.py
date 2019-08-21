import argparse
import sys
import traceback
import pkg_resources

from test_junkie.cli.cli_audit import CliAudit
from test_junkie.cli.cli_hq import TestJunkieHQ
from test_junkie.cli.cli_utils import CliUtils
from test_junkie.constants import DocumentationLinks, CliConstants, Undefined
from test_junkie.errors import BadCliParameters


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
hq\t Allows integration with Test Junkie HQ
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

    def hq(self):
        parser = argparse.ArgumentParser(
            description="",
            usage="""tj hq COMMAND

Utility to help with integration of Test Junkie HQ.
Test Junkie HQ - Modern UI for Modern Testing Framework 
where you can initiate test runs and analyze test 
results and much, much more!

Commands:
master\t Allows to setup master service on a node
agent\t Allows to add a Test Junkie agent to a project


Use: tj hq COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        args = parser.parse_args(sys.argv[2:3])
        TestJunkieHQ(args.command, sys.argv[3:])

    def run(self):
        parser = argparse.ArgumentParser(description='Run tests from command line',
                                         usage="tj run [OPTIONS]")

        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Test Junkie will only run suites provided, "
                                 "given that they are found in the SOURCE")

        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")

        parser.add_argument("--config", type=str, default=Undefined,
                            help="Provide your own config FILE with settings for test execution.")

        CliUtils.add_standard_tj_args(parser)

        args = parser.parse_args(sys.argv[2:])

        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.cli_runner import CliRunner
        try:
            tj = CliRunner(sources=args.sources, ignore=[".git"], suites=args.suites,
                           code_cov=args.code_cov, cov_rcfile=args.cov_rcfile, guess_root=args.guess_root,
                           config=args.config)
            tj.scan()
        except BadCliParameters as error:
            print("[{status}] {error}".format(status=CliUtils.format_color_string("ERROR", "red"), error=error))
            return
        tj.run_suites(args)

    def audit(self):
        parser = argparse.ArgumentParser(description='Scan and display aggregated and/or filtered test information',
                                         usage="""tj audit [COMMAND] [OPTIONS]

Aggregate, pivot, and display data about your tests.

Commands:
suites\t\t Pivot test information from suite's perspective
features\t Pivot test information from feature's perspective
components\t Pivot test information from component's perspective
tags\t\t Pivot test information from tag's perspective
owners\t\t Pivot test information from owner's perspective

usage: tj audit [COMMAND] [OPTIONS]
""")
        parser.add_argument('command', help='command to run')

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

        parser.add_argument("--no-tags", action="store_true", default=False,
                            help="Aggregate data only for tests that do not have tags defined")

        parser.add_argument("-x", "--suites", nargs="+", default=None,
                            help="Test Junkie will only run suites provided, "
                                 "given that they are found in the SOURCE")

        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")

        CliUtils.add_standard_tj_args(parser, audit=True)

        if len(sys.argv) >= 3:
            args = parser.parse_args(sys.argv[2:])
            command = args.command
            if command not in ["suites", "features", "components", "tags", "owners"]:
                print("[{status}]\t\'{command}\' is not a test-junkie command\n".format(
                    status=CliUtils.format_color_string(value="ERROR", color="red"),
                    command=command))
                parser.print_help()
                exit(120)
            else:
                if args.verbose:
                    from test_junkie.debugger import LogJunkie
                    LogJunkie.enable_logging(10)

                from test_junkie.cli.cli_runner import CliRunner
                try:
                    tj = CliRunner(sources=args.sources, ignore=[".git"], suites=args.suites,
                                   guess_root=args.guess_root)
                    tj.scan()
                except BadCliParameters as error:
                    print("[{status}] {error}".format(status=CliUtils.format_color_string("ERROR", "red"), error=error))
                    return
                aggregator = CliAudit(suites=tj.suites, args=args)
                aggregator.aggregate()
                aggregator.print_results()
                return
        else:
            print("[{status}]\tDude, what do you want to audit?".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
        parser.print_help()

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
                    from test_junkie.cli.cli_config import CliConfig
                    return CliConfig(CliConstants.TJ_CONFIG_NAME, command, sys.argv)
                elif command not in ["-h"]:
                    print("[{status}]\t\'{command}\' is not a test-junkie command\n".format(
                          status=CliUtils.format_color_string(value="ERROR", color="red"),
                          command=command))
            else:
                print("[{status}]\tDude, what do you want to do with the config?".format(
                      status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
        except:
            if "SystemExit:" not in traceback.format_exc():
                CliUtils.print_color_traceback()
                parser.print_help()
                exit(120)

    def version(self):
        print("Test Junkie {} (Python{})\n{}".format(pkg_resources.require("test-junkie")[0].version,
                                                     sys.version_info[0],
                                                     DocumentationLinks.DOMAIN))


if "__main__" == __name__:

    Cli()
