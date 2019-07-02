import argparse
import ast
import imp
import inspect
import os
import shutil
import sys
import time
import re
from shutil import copyfile

from setuptools.glob import glob

from test_junkie.cli.cli import CliUtils
from test_junkie.cli.cli_config import Config
from test_junkie.constants import CliConstants
from test_junkie.errors import BadCliParameters
from test_junkie.runner import Runner
from test_junkie.settings import Settings


class CliRunner:

    __REGEX_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite as.*?\n"
    __REGEX_NO_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite.*?\n"

    def __init__(self, sources, ignore, suites):

        self.__sources = sources
        self.tjignore = ignore
        self.detected_suites = {}
        self.suites = []
        self.requested_suites = suites
        self.config = Config(config_name=CliConstants.TJ_CONFIG_NAME)

    @property
    def sources(self):
        if self.__sources == Settings.UNDEFINED:
            self.__sources = self.config.get_value("sources")
            self.__sources = ast.literal_eval(self.__sources)
        if self.__sources == Settings.UNDEFINED or not isinstance(self.__sources, list):
            raise BadCliParameters("Sources is a required parameter. You can set it in the config via tj config "
                                   "update -s / --sources to persist or pass it in directly to the command you "
                                   "are running via -s / --sources")
        return self.__sources

    def __find_and_register_suite(self, _suite_alias, _source, _file_path):

        def load_module(_decorated_classes):

            module_name = os.path.splitext(os.path.basename(_file_path))[0]
            try:
                module = imp.load_source(module_name, _file_path)
            except ImportError as error:
                splitter = "{sep}{dir}{sep}".format(
                    sep=os.sep, dir=str(error).replace("No module named ", "").split(".")[0].replace("'", ""))
                if splitter in _file_path:
                    assumed_root = _file_path.split(splitter)[0]
                    print("[{status}] Import error: {error}"
                          .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                                  error=error))
                    print("[{status}] Trying again with assumption that this is your project root: {assumed_root}"
                          .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                                  assumed_root=CliUtils.format_color_string(value=assumed_root, color="yellow")))
                    print("[{status}] This may or may not work but if the import error is for a package in your "
                          "project, make sure that project is included in {pythonpath}."
                          .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                                  pythonpath=CliUtils.format_color_string(value="PYTHONPATH", color="yellow")))
                    sys.path.insert(0, assumed_root)
                    module = imp.load_source(module_name, _file_path)
                else:
                    print("[{status}] You have an Import Error in one of your suites. Try again once its resolved."
                          .format(status=CliUtils.format_color_string(value="WARNING", color="yellow")))
                    print("[{status}] If the import error is for a package in your "
                          "project, make sure that project is included in {pythonpath}."
                          .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                                  pythonpath=CliUtils.format_color_string(value="PYTHONPATH", color="yellow")))
                    raise
            for name, data in inspect.getmembers(module):

                if name in _decorated_classes and inspect.isclass(data):
                    if not self.requested_suites or \
                            (self.requested_suites and name in self.requested_suites):
                        self.suites.append(data)

        matches = re.findall("@{alias}((.|\n)*?):\n".format(alias=_suite_alias), _source)
        decorated_classes = []
        for match in matches:
            if isinstance(match, tuple):
                for item in match:
                    if "\nclass " in item:
                        decorated_classes.append(item.split("\nclass ")[-1].strip())
            else:
                if "\nclass " in match:
                    decorated_classes.append(match.split("\nclass ")[-1].strip())
        load_module(decorated_classes)

    def __skip(self, source, directory):

        if source not in directory:
            return True

        for ignored_item in self.tjignore:
            if ignored_item in directory:
                return True
        return False

    def scan(self):

        def parse_file(_file):

            with open(_file) as doc:

                source = doc.read()

                suite_imported_as_alias = re.findall(CliRunner.__REGEX_ALIAS_IMPORT, source)
                if suite_imported_as_alias:
                    suite_alias = suite_imported_as_alias[-1].split("Suite")[-1].split("as")[-1].split(",")[0].strip()
                    self.__find_and_register_suite(suite_alias, source, doc.name)
                    return True

                suite_imported = re.findall(CliRunner.__REGEX_NO_ALIAS_IMPORT, source)
                if suite_imported:
                    self.__find_and_register_suite("Suite", source, doc.name)
                    return True

        print("\n[{status}] Scanning: {location} ..."
              .format(location=CliUtils.format_color_string(value=",".join(self.sources), color="green"),
                      status=CliUtils.format_color_string(value="INFO", color="blue")))
        start = time.time()
        try:
            for source in self.sources:
                if source.endswith(".py"):
                    parse_file(source)
                else:
                    for dirName, subdirList, fileList in os.walk(source, topdown=True):

                        if self.__skip(source, dirName):
                            continue

                        for file_path in glob(os.path.join(os.path.dirname(dirName+"\\"), "*.py")):
                            if parse_file(file_path)is True:
                                continue
        except:
            print("[{status}] Unexpected error during scan for test suites.".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            CliUtils.print_color_traceback()
            exit(120)
        print("[{status}] Scan finished in: {time} seconds. Found: {suites} suite(s)."
              .format(status=CliUtils.format_color_string(value="INFO", color="blue"),
                      time="{0:.2f}".format(time.time() - start), suites=len(self.suites)))

    def run_suites(self, args):

        def tags():
            config = {"run_on_match_all": args.run_on_match_all,
                      "run_on_match_any": args.run_on_match_any,
                      "skip_on_match_all": args.skip_on_match_all,
                      "skip_on_match_any": args.skip_on_match_any}
            for prop, value in config.items():
                if value is not None:
                    return config
            return None

        def update_code_cov_config():

            tj_config = Config(config_name=CliConstants.TJ_CONFIG_NAME)
            shutil.copy2(tj_config.path, Config.get_config_path(CliConstants.TJ_COV_CONFIG_NAME))
            # Initiating tj_cov_config afterwards because otherwise there is a file lock and copy does not work
            tj_cov_config = Config(config_name=CliConstants.TJ_COV_CONFIG_NAME)

            for option in ["test_multithreading_limit",
                           "suite_multithreading_limit",
                           "html_report",
                           "xml_report",
                           "monitor_resources",
                           "tests",
                           "features",
                           "components",
                           "owners",
                           "run_on_match_all",
                           "run_on_match_any",
                           "skip_on_match_all",
                           "skip_on_match_any",
                           "sources"]:
                explicit_value = getattr(args, option)
                if explicit_value != Settings.UNDEFINED:
                    tj_cov_config.set_value(option, explicit_value)

        if args.code_cov:
            import subprocess
            update_code_cov_config()

            run_command = ['coverage', 'run', __file__]
            if args.cov_rcfile != Settings.UNDEFINED:
                run_command.append("--rcfile")
                run_command.append(args.cov_rcfile)
            if args.verbose:
                run_command.append("-v")

            for cmd in [run_command]:
                process = subprocess.Popen(cmd, shell=True)
                process.communicate()
                if process.wait():
                    exit(120)
            return

        if self.suites:
            print("[{status}] Running tests ...\n"
                  .format(status=CliUtils.format_color_string(value="INFO", color="blue")))
            try:
                runner = Runner(suites=self.suites,
                                html_report=args.html_report,
                                xml_report=args.xml_report,
                                config=Config.get_config_path(CliConstants.TJ_CONFIG_NAME))
                runner.run(test_multithreading_limit=args.test_multithreading_limit,
                           suite_multithreading_limit=args.suite_multithreading_limit,
                           tests=args.tests,
                           owners=args.owners,
                           components=args.components,
                           features=args.features,
                           tag_config=tags())
            except:
                CliUtils.print_color_traceback()
                exit(120)


if "__main__" == __name__:

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Enable verbose mode for debugging")
    args = parser.parse_args()
    if args.verbose:
        from test_junkie.debugger import LogJunkie
        LogJunkie.enable_logging(10)

    config = Config(config_name=CliConstants.TJ_COV_CONFIG_NAME)
    sources = ast.literal_eval(config.get_value("sources"))
    scanner = CliRunner(sources, [".git"], None)
    scanner.scan()
    if scanner.suites:
        print("[{status}] Running tests ...\n"
              .format(status=CliUtils.format_color_string(value="INFO", color="blue")))
        try:
            runner = Runner(suites=scanner.suites, config=config.path)
            runner.run()
            print("[{status}] Coverage reports can be accessed via coverage cli. Try \"coverage report -m\". "
                  "For more see \"coverage -h\"\n"
                  .format(status=CliUtils.format_color_string(value="TIP", color="blue")))
        except:
            CliUtils.print_color_traceback()
            exit(120)
    shutil.copy2("C:\\Users\\aspir\\AppData\\Local\\Test-Junkie\\Test-Junkie\\.tj.cfg",
                 "C:\\Users\\aspir\\AppData\\Local\\Test-Junkie\\Test-Junkie\\.tj-cov.cfg")

    # tj_cov_config = Config(config_name=CliConstants.TJ_COV_CONFIG_NAME)
    # tj_config = Config(config_name=CliConstants.TJ_CONFIG_NAME)
    # tj_cov_config.restore(tj_config.read())
    # print(tj_config.path)
    # print(tj_cov_config.path)
    # shutil.copy2(tj_config.path, tj_cov_config.path)