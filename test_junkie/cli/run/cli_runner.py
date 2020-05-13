import ast
import imp
import inspect
import os
import sys
import threading
import time
import re
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console
from rich.progress import track
from setuptools.glob import glob

from test_junkie.cli.config.Config import Config
from test_junkie.cli.utils import Color
from test_junkie.constants import CliConstants, Undefined, DocumentationLinks
from test_junkie.debugger import suppressed_stdout
from test_junkie.decorators import synchronized
from test_junkie.errors import BadCliParameters
from test_junkie.runner import Runner



class CliRunner:

    __REGEX_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite as.*?\n"
    __REGEX_NO_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite.*?\n"
    __SCANNER_THREADS = []

    def __init__(self, sources, ignore, suites, **kwargs):

        self.__sources = sources
        self.__code_cov = kwargs.get("code_cov", None)
        self.__cov_rcfile = kwargs.get("cov_rcfile", None)
        self.__guess_root = not kwargs.get("no_guess_root", False)
        self.__execution_config = kwargs.get("config", Undefined)

        self.tjignore = ignore
        self.detected_suites = {}
        self.detected_issues_during_scan = []
        self.suites = []
        self.requested_suites = suites
        self.__config = Config(config_name=CliConstants.TJ_CONFIG_NAME if
                               isinstance(self.__execution_config, Undefined) or self.__execution_config == Undefined
                               else self.__execution_config)
        self.coverage = None
        if self.code_cov:
            import coverage
            if self.cov_rcfile is not None:
                self.coverage = coverage.Coverage(omit="*{sep}test_junkie{sep}*".format(sep=os.sep),
                                                  config_file=self.cov_rcfile)
            else:
                self.coverage = coverage.Coverage(omit="*{sep}test_junkie{sep}*".format(sep=os.sep))
            self.coverage.start()

        self.console = Console()

    @property
    def sources(self):
        if isinstance(self.__sources, Undefined):
            self.__sources = ast.literal_eval(self.__config.get_value("sources"))
        if isinstance(self.__sources, Undefined) or not isinstance(self.__sources, list):
            raise BadCliParameters("Sources is a required parameter. You can set it in the config via tj config "
                                   "update -s / --sources to persist or pass it in directly to the command you "
                                   "are running via -s / --sources")
        return self.__sources

    @property
    def code_cov(self):
        if isinstance(self.__code_cov, Undefined):
            self.__code_cov = ast.literal_eval(self.__config.get_value("code_cov", default=False))
        return self.__code_cov

    @property
    def cov_rcfile(self):
        if isinstance(self.__cov_rcfile, Undefined):
            self.__cov_rcfile = self.__config.get_value("cov_rcfile", default=None)
            if self.__cov_rcfile == "None":
                self.__cov_rcfile = None
        return self.__cov_rcfile

    @property
    def guess_root(self):
        if isinstance(self.__guess_root, Undefined):
            self.__guess_root = self.__config.get_value("guess_root", default=False)
        return self.__guess_root

    @property
    def execution_config(self):
        if isinstance(self.__execution_config, Undefined):
            self.__execution_config = Config.get_config_path(CliConstants.TJ_CONFIG_NAME)
        return self.__execution_config

    @staticmethod
    def start_in_a_thread(target, args):

        def get_active_count():
            active = 0
            for thread in CliRunner.__SCANNER_THREADS:
                if thread.isAlive():
                    active += 1
                else:
                    CliRunner.__SCANNER_THREADS.remove(thread)
            return active

        while get_active_count() > 50:
            time.sleep(1)
        new_thread = threading.Thread(target=target, args=args)
        CliRunner.__SCANNER_THREADS.append(new_thread)
        new_thread.start()
        return new_thread

    def __find_and_register_suite(self, _suite_alias, _source, _file_path):

        def guess_project_root(path, _module_name):

            possibility = "{}".format(Path(path).parent)
            try:
                sys.path.insert(0, possibility)
                return imp.load_source(_module_name, _file_path)
            except KeyboardInterrupt:
                print("(Ctrl+C) Exiting!")
                exit(12)
            except ImportError as error:
                if len(possibility.split(os.sep)) > 2:
                    return guess_project_root(possibility, _module_name)
                raise

        @synchronized()
        def load_module(_decorated_classes):
            module_name = os.path.splitext(os.path.basename(_file_path))[0]
            try:
                try:
                    with suppressed_stdout(suppress=True):
                        module = imp.load_source(module_name, _file_path)
                except ImportError as error:
                    if self.guess_root:
                        module = guess_project_root(_file_path, module_name)
                    else:
                        raise
                for name, data in inspect.getmembers(module):
                    if name in _decorated_classes and inspect.isclass(data):
                        if not self.requested_suites or \
                                (self.requested_suites and name in self.requested_suites):
                            self.suites.append(data)
            except Exception as exception:
                self.detected_issues_during_scan.append({"exception": exception,
                                                         "module": module_name,
                                                         "file": _file_path})

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

        if directory.startswith("."):
            return True

        if source not in directory:
            return True

        for ignored_item in self.tjignore:
            if ignored_item in directory:
                return True
        return False

    def scan(self):

        def eval_errors():
            if self.detected_issues_during_scan:
                self.console.print("[[[red]ATTENTION[/red]]] Detected {} issue(s)"
                                   .format(len(self.detected_issues_during_scan)))
                for issue in self.detected_issues_during_scan:
                    self.console.print(f"Module: '{issue['file']}'\n\t|__ [red]{issue['exception']}[/red]\n")
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
                    CliRunner.start_in_a_thread(target=self.__find_and_register_suite,
                                                args=(suite_alias, __source[0], __source[1].name))
                    return True

                suite_imported = re.findall(CliRunner.__REGEX_NO_ALIAS_IMPORT, __source[0])
                if suite_imported:
                    CliRunner.start_in_a_thread(target=self.__find_and_register_suite,
                                                args=("Suite", __source[0], __source[1].name))
                    return True

        try:
            self.console.print("\n[[[bold blue]INFO[/bold blue]]] Scanning for tests...")
            self.detected_issues_during_scan = []
            start = time.time()
            for source in self.sources:
                if source.endswith(".py"):
                    parse_file(source)
                else:
                    for dirName, subdirList, fileList in track(list(os.walk(source, topdown=True)),
                                                               description=f"Scanning: [blue]{source}[/blue]"):

                        if self.__skip(source, dirName):
                            continue

                        for file_path in glob(os.path.join(os.path.dirname(dirName+"\\"), "*.py")):
                            if parse_file(file_path) is True:
                                continue

            for thread in CliRunner.__SCANNER_THREADS:
                thread.join()
            print("[{status}] Scan finished in: {time} seconds. Found: {suites} suite(s)."
                  .format(status=Color.format_string(value="INFO", color="blue"),
                          time="{0:.2f}".format(time.time() - start),
                          suites=Color.format_bold_string(len(self.suites))))
            eval_errors()
        except KeyboardInterrupt:
            print("(Ctrl+C) Exiting!")
            exit(12)
        except BadCliParameters as err:
            print("[{status}] {error}.".format(status=Color.format_string(value="ERROR", color="red"),
                                               error=err))
            exit(120)
        except:
            print("[{status}] Unexpected error during scan for test suites.".format(
                status=Color.format_string(value="ERROR", color="red")))
            Color.print_traceback()
            exit(120)

    def run_suites(self, **args):

        def tags():
            config = {"run_on_match_all": args["run_on_match_all"],
                      "run_on_match_any": args["run_on_match_any"],
                      "skip_on_match_all": args["skip_on_match_all"],
                      "skip_on_match_any": args["skip_on_match_any"]}
            for prop, value in config.items():
                if value is not None:
                    return config
            return None

        if self.suites:
            print("[{status}] Running tests ..."
                  .format(status=Color.format_string(value="INFO", color="blue")))
            try:
                runner = Runner(suites=self.suites,
                                html_report=args["html_report"],
                                xml_report=args["xml_report"],
                                config=self.execution_config,
                                show_progress=True)
                runner.run(test_multithreading_limit=args["test_multithreading_limit"],
                           suite_multithreading_limit=args["suite_multithreading_limit"],
                           tests=args["tests"],
                           owners=args["owners"],
                           components=args["components"],
                           features=args["features"],
                           tag_config=tags(),
                           quiet=not args["no_quiet"])
            except KeyboardInterrupt:
                print("(Ctrl+C) Exiting!")
                exit(12)
            except:
                print("[{status}] Unexpected error during test execution.".format(
                      status=Color.format_string(value="ERROR", color="red")))
                Color.print_traceback()
                exit(120)
            finally:
                if self.coverage is not None:
                    self.coverage.stop()
                    self.coverage.save()
                    import coverage
                    try:
                        print("[{status}] Code coverage report:".format(
                            status=Color.format_string(value="INFO", color="blue")))
                        self.coverage.report(show_missing=True, skip_covered=True)
                        print("[{status}] TJ uses Coverage.py. Control it with --cov-rcfile, "
                              "see {link}".format(status=Color.format_string(value="TIP", color="blue"),
                                                  link=DocumentationLinks.COVERAGE_CONFIG_FILE))
                    except coverage.misc.CoverageException:
                        Color.print_traceback()
                        exit(120)
            return
