import argparse
import sys

import pkg_resources

# sys.path.insert(1, "E:/Development/test_junkie/")

from test_junkie.constants import DocumentationLinks


class Cli(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description="",
            usage="""tj COMMAND

Modern Testing Framework

Commands:
run\t Run tests in any directory recursively via cmd
scan\t Scans for tests in any directory recursively via cmd 
config\t Configure Test Junkie
version\t Display current version

Use: tj COMMAND -h to display COMMAND specific help
""")
        parser.add_argument('command', help='command to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('test-junkie: \'{}\' is not a test-junkie command\n'.format(args.command))
            parser.print_help()
            exit(1)
        if args.command:
            # use dispatch pattern to invoke method with same name
            getattr(self, args.command)()

    def run(self):
        parser = argparse.ArgumentParser(description='Run tests from command line',
                                         usage="tj run -s SOURCE [OPTIONS]")

        parser.add_argument("-s", "--source", type=str, default=None, required=True,  # unless defined in the config
                            help="Path to DIRECTORY where you have your tests. "
                                 "Test Junkie will traverse this directory looking for test suites")

        parser.add_argument("-T", "--test_multithreading_limit", type=int, default=None,
                            help="Enables parallel test processing with allocated N number of threads")

        parser.add_argument("-S", "--suite_multithreading_limit", type=int, default=None,
                            help="Enables parallel suite processing with allocated N number of threads")

        parser.add_argument("-f", "--features", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the features listed")

        parser.add_argument("-c", "--components", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the components listed")

        parser.add_argument("-o", "--owners", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the owners listed")

        parser.add_argument("-m", "--monitor_resources", action="store_true", default=None,
                            help="Enables CPU & MEM monitoring")

        parser.add_argument("--html", type=str, default=None,
                            help="Path to FILE. This will enable HTML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("--xml", type=str, default=None,
                            help="Path to FILE. This will enable XML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("-l", "--run_on_match_all", nargs="+", default=None,
                            help="Test Junkie will RUN tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-k", "--run_on_match_any", nargs="+", default=None,
                            help="Test Junkie will RUN tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-j", "--skip_on_match_all", nargs="+", default=None,
                            help="Test Junkie will SKIP tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-g", "--skip_on_match_any", nargs="+", default=None,
                            help="Test Junkie will SKIP tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-v", "--verbose", action="store_true", default=False,
                            help="Enables Test Junkie's logs for debugging purposes")

        args = parser.parse_args(sys.argv[2:])

        if args.verbose:
            from test_junkie.debugger import LogJunkie
            LogJunkie.enable_logging(10)

        from test_junkie.cli.runner_manager import RunnerManager
        tj = RunnerManager(root=args.source, ignore=[".git"])
        tj.scan()
        tj.run_suites(args)

    def scan(self):

        parser = argparse.ArgumentParser(usage="""tj scan [OPTIONS]

Scan for tests from command line

Commands:
show\t Display current configuration for Test-Junkie
update\t Update configuration settings for individual properties via cli 
restore\t Will restore config to it\'s original values

Use: tj config COMMAND -h to display COMMAND specific help
""")

        parser.add_argument("-s", "--source", type=str, default=None, required=True,  # unless defined in the config
                            help="Path to DIRECTORY where you have your tests. "
                                 "Test Junkie will traverse this directory looking for test suites")

        parser.add_argument("-f", "--features", nargs="+",
                            help="Will filter out all of the tests that do not belong to the features listed")

        parser.add_argument("-c", "--components", nargs="+",
                            help="Will filter out all of the tests that do not belong to the components listed")

        parser.add_argument("-o", "--owners", nargs="+",
                            help="Will filter out all of the tests that do not belong to the owners listed")

        args = parser.parse_args(sys.argv[2:])
        from test_junkie.cli.runner_manager import RunnerManager
        tj = RunnerManager(root=args.source, ignore=[".git"])
        tj.scan()

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
            command = sys.argv[2:3][0]
            if command in ["show", "update", "restore"]:
                from test_junkie.cli.config_manager import ConfigManager
                return ConfigManager(command, sys.argv)
            else:
                parser.print_help()
        except:
            parser.print_help()


    def version(self):
        print("Test Junkie {}".format(pkg_resources.require("test-junkie")[0].version))


class CliUtils:

    def __init__(self):

        pass

    @staticmethod
    def add_standard_tj_args(parser):

        parser.add_argument("-T", "--test_multithreading_limit", type=int, default=None,
                            help="Enables parallel test processing with allocated N number of threads")

        parser.add_argument("-S", "--suite_multithreading_limit", type=int, default=None,
                            help="Enables parallel suite processing with allocated N number of threads")

        parser.add_argument("-f", "--features", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the features listed")

        parser.add_argument("-c", "--components", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the components listed")

        parser.add_argument("-o", "--owners", nargs="+", default=None,
                            help="Will filter out all of the tests that do not belong to the owners listed")

        parser.add_argument("-m", "--monitor_resources", action="store_true", default=None,
                            help="Enables CPU & MEM monitoring")

        parser.add_argument("--html", type=str, default=None,
                            help="Path to FILE. This will enable HTML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("--xml", type=str, default=None,
                            help="Path to FILE. This will enable XML report generation and when ready, "
                                 "the report will be saved to the specified file")

        parser.add_argument("-l", "--run_on_match_all", nargs="+", default=None,
                            help="Test Junkie will RUN tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-k", "--run_on_match_any", nargs="+", default=None,
                            help="Test Junkie will RUN tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-j", "--skip_on_match_all", nargs="+", default=None,
                            help="Test Junkie will SKIP tests that match ALL of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))

        parser.add_argument("-g", "--skip_on_match_any", nargs="+", default=None,
                            help="Test Junkie will SKIP tests that match ANY of the tags. Read more about it: {link}"
                            .format(link=DocumentationLinks.TAGS))
