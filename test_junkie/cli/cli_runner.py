import ast
import imp
import inspect
import os
import sys
import time
import re
from contextlib import contextmanager

from setuptools.glob import glob

from test_junkie.cli.cli import CliUtils
from test_junkie.constants import CliConstants, Undefined
from test_junkie.debugger import suppressed_stdout
from test_junkie.errors import BadCliParameters
from test_junkie.runner import Runner
from test_junkie.cli.cli_config import Config


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
        if self.__sources == Undefined:
            self.__sources = self.config.get_value("sources")
            self.__sources = ast.literal_eval(self.__sources)
        if self.__sources == Undefined or not isinstance(self.__sources, list):
            raise BadCliParameters("Sources is a required parameter. You can set it in the config via tj config "
                                   "update -s / --sources to persist or pass it in directly to the command you "
                                   "are running via -s / --sources")
        return self.__sources

    def __find_and_register_suite(self, _suite_alias, _source, _file_path):

        def load_module(_decorated_classes):

            module_name = os.path.splitext(os.path.basename(_file_path))[0]
            try:
                with suppressed_stdout(suppress=True):
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
                    print("[{status}] Make sure you can run files that have issues yourself through CMD before you run "
                          "it via TJ.".format(status=CliUtils.format_color_string(value="WARNING", color="yellow")))
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

        @contextmanager
        def open_file(_file):
            if sys.version_info[0] < 3:
                with open(_file) as _doc:
                    _source = _doc.read()
                    yield (_source, _doc)
            else:
                with open(_file, encoding="utf-8") as _doc:
                    _source = _doc.read()
                    yield (_source, _doc)

        def parse_file(_file):

            with open_file(_file) as __source:

                suite_imported_as_alias = re.findall(CliRunner.__REGEX_ALIAS_IMPORT, __source[0])
                if suite_imported_as_alias:
                    suite_alias = suite_imported_as_alias[-1].split("Suite")[-1].split("as")[-1].split(",")[0].strip()
                    self.__find_and_register_suite(suite_alias, __source[0], __source[1].name)
                    return True

                suite_imported = re.findall(CliRunner.__REGEX_NO_ALIAS_IMPORT, __source[0])
                if suite_imported:
                    self.__find_and_register_suite("Suite", __source[0], __source[1].name)
                    return True

        try:
            print("\n[{status}] Scanning: {location} ..."
                  .format(location=CliUtils.format_color_string(value=",".join(self.sources), color="green"),
                          status=CliUtils.format_color_string(value="INFO", color="blue")))
            start = time.time()
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
            print("[{status}] Scan finished in: {time} seconds. Found: {suites} suite(s)."
                  .format(status=CliUtils.format_color_string(value="INFO", color="blue"),
                          time="{0:.2f}".format(time.time() - start),
                          suites=CliUtils.format_bold_string(len(self.suites))))
        except KeyboardInterrupt:
            print("(Ctrl+C) Exiting!")
            exit(12)
        except BadCliParameters as err:
            print("[{status}] {error}.".format(status=CliUtils.format_color_string(value="ERROR", color="red"),
                                               error=err))
            exit(120)
        except:
            print("[{status}] Unexpected error during scan for test suites.".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            CliUtils.print_color_traceback()
            exit(120)

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

        if self.suites:
            print("[{status}] Running tests ...\n"
                  .format(status=CliUtils.format_color_string(value="INFO", color="blue")))
            if args.code_cov:
                import coverage
                cov = coverage.Coverage(omit="*{sep}test_junkie{sep}*".format(sep=os.sep),
                                        config_file=args.cov_rcfile)
                cov.start()
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
                           tag_config=tags(),
                           quiet=args.quiet)
            except KeyboardInterrupt:
                print("(Ctrl+C) Exiting!")
                exit(12)
            except:
                print("[{status}] Unexpected error during test execution.".format(
                      status=CliUtils.format_color_string(value="ERROR", color="red")))
                CliUtils.print_color_traceback()
                exit(120)
            finally:
                if args.code_cov:
                    cov.stop()
                    cov.save()
            if args.code_cov:
                try:
                    cov.report(show_missing=True, skip_covered=True)
                    print("[{status}] TJ uses Coverage.py. Control it with --cov-rcfile, "
                          "see https://coverage.readthedocs.io/en/v4.5.x/config.html"
                          .format(status=CliUtils.format_color_string(value="TIP", color="blue")))
                except coverage.misc.CoverageException:
                    pass
            return
