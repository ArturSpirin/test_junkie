import traceback

from colorama import Fore, Style

from test_junkie.constants import Undefined, DocumentationLinks


class CliUtils:

    __INITIALIZED = False

    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    def __init__(self):

        pass

    @staticmethod
    def add_standard_tj_args(parser, audit=False):
        """
        Generic parser args used to configure execution or set config settings
        """
        if not audit:
            parser.add_argument("-T", "--test_multithreading_limit", type=int, default=Undefined,
                                help="Test level multi threading allows to run multiple tests concurrently.")

            parser.add_argument("-S", "--suite_multithreading_limit", type=int, default=Undefined,
                                help="Suite level multi threading allows to run multiple suites concurrently.")

            parser.add_argument("-t", "--tests", nargs="+", default=Undefined,
                                help="Test Junkie can run specific tests. "
                                     "Provide the names of the tests that you want to execute/audit.")

        parser.add_argument("-f", "--features", nargs="+", default=Undefined,
                            help="Test suites can be defined with a feature that they are testing. "
                                 "Use features to narrow down execution/audit of test suites only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.FEATURES))

        parser.add_argument("-c", "--components", nargs="+", default=Undefined,
                            help="Tests can be defined with a component that they are testing. "
                                 "Use components to narrow down execution/audit of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.COMPONENTS))

        parser.add_argument("-o", "--owners", nargs="+", default=Undefined,
                            help="Tests & test suites can be defined with an assignee. "
                                 "Use owners to narrow down execution/audit of tests only to those that "
                                 "match this filter. Learn more @ {link}".format(link=DocumentationLinks.ASSIGNEES))

        if not audit:
            parser.add_argument("-m", "--monitor_resources", action="store_true", default=Undefined,
                                help="Test Junkie can track resource usage for CPU & Memory as it runs tests")

            parser.add_argument("--html_report", type=str, default=Undefined,
                                help="Path to FILE. This will enable HTML report generation and when ready, "
                                     "the report will be saved to the specified file")

            parser.add_argument("--xml_report", type=str, default=Undefined,
                                help="Path to FILE. This will enable XML report generation and when ready, "
                                     "the report will be saved to the specified file")

            parser.add_argument("-l", "--run_on_match_all", nargs="+", default=Undefined,
                                help="Test Junkie will RUN tests that match ALL of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-k", "--run_on_match_any", nargs="+", default=Undefined,
                                help="Test Junkie will RUN tests that match ANY of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-j", "--skip_on_match_all", nargs="+", default=Undefined,
                                help="Test Junkie will SKIP tests that match ALL of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-g", "--skip_on_match_any", nargs="+", default=Undefined,
                                help="Test Junkie will SKIP tests that match ANY of the tags. Read more about it: {link}"
                                .format(link=DocumentationLinks.TAGS))

            parser.add_argument("-q", "--quiet", action="store_true", default=Undefined,
                                help="Suppress all standard output from tests")

            parser.add_argument("--code-cov", action="store_true", default=Undefined,
                                help="Measure code coverage")

            parser.add_argument("--cov-rcfile", type=str, default=Undefined,
                                help="Path to configuration FILE for coverage.py "
                                     "See {link}".format(link=DocumentationLinks.COVERAGE_CONFIG_FILE))
        else:
            parser.add_argument("-l", "--tags", nargs="+", default=Undefined,
                                help="Test Junkie will audit tests that match those tags.")

        parser.add_argument("-s", "--sources", nargs="+", default=Undefined,
                            help="Paths to DIRECTORY or FILE where you have your tests. "
                                 "Test Junkie will traverse this source(s) looking for test suites")

        parser.add_argument("--guess-root", action="store_true", default=Undefined,
                            help="If your project is not part of the PYTHONPATH, you will get an error when running "
                                 "it via command line. If this flag is used, TJ will try to guess the root directory "
                                 "and temporary add it to the path. Usually not recommended.")

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

        parser.add_argument("-t", "--tests", nargs="+", default=Undefined,
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
        parser.add_argument("-q", "--quiet", action="store_true", default=False,
                            help="Suppress all standard output from tests")
        parser.add_argument("--code-cov", action="store_true", default=False,
                            help="Measure code coverage")
        parser.add_argument("--cov-rcfile", action="store_true", default=False,
                            help="Path to configuration FILE for coverage.py "
                                 "See {link}".format(link=DocumentationLinks.COVERAGE_CONFIG_FILE))
        parser.add_argument("--guess-root", action="store_true", default=False,
                            help="If your project is not part of the PYTHONPATH, you will get an error when running "
                                 "it via command line. If this flag is used, TJ will try to guess the root directory "
                                 "and temporary add it to the path. Usually not recommended.")

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
    def format_bold_string(value):
        CliUtils.__initialize()
        return "{bold}{value}{end}".format(bold=CliUtils.BOLD, value=value, end=CliUtils.END)