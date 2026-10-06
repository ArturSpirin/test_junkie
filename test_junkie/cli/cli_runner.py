import glob
import hashlib
import importlib.util
import inspect
import os
import sys
import time
import re

from test_junkie.builder import Builder
from test_junkie.cli.cli import CliUtils
from test_junkie.constants import CliConstants, Undefined, DocumentationLinks, TestCategory
from test_junkie.debugger import suppressed_stdout
from test_junkie.errors import BadCliParameters
from test_junkie.metrics import Aggregator
from test_junkie.runner import Runner
from test_junkie.cli.cli_config import Config


def _module_name(file_path):
    """
    Name to load a suite file under. Every file used to be loaded under its bare file name, so `tests/a/login.py` and
    `tests/b/login.py` were both `login` (the second replaced the first in sys.modules) and a suite file named like an
    importable module (`json.py`, `logging.py`, ...) replaced that module for the whole process.
    The bare name is still used when it's free; otherwise the path relative to the working directory (`tests.b.login`)
    """
    file_path = os.path.abspath(file_path)

    def free(name):
        module = sys.modules.get(name)
        if module is not None:
            return os.path.abspath(getattr(module, "__file__", None) or "") == file_path
        if "." in name:
            return True
        try:  # importable from elsewhere (stdlib, an installed package) even though nothing imported it yet
            spec = importlib.util.find_spec(name)
        except (ImportError, ValueError):
            return True
        return spec is None or os.path.abspath(spec.origin or "") == file_path

    name = os.path.splitext(os.path.basename(file_path))[0]
    if free(name):
        return name
    relative = os.path.splitext(os.path.relpath(file_path))[0] if os.path.splitdrive(file_path)[0].lower() == \
        os.path.splitdrive(os.getcwd())[0].lower() else os.path.splitext(file_path)[0]
    dotted = ".".join(re.sub(r"\W", "_", part) for part in relative.split(os.sep) if part not in ("", ".."))
    if dotted and free(dotted):
        return dotted
    return "{}_{}".format(dotted or name, hashlib.md5(file_path.encode("utf-8")).hexdigest()[:8])


def _load_source(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class CliRunner:

    # cheap text pre-filter only - which classes are suites is decided by importing the file and checking the
    # Builder's roster, so base classes, comments, multi-line imports etc. don't matter
    __REGEX_SUITE_ALIAS = re.compile(r"\bSuite\s+as\s+(\w+)")

    def __init__(self, sources, ignore, suites, **kwargs):

        self.__sources = sources
        self.__code_cov = kwargs.get("code_cov", Undefined)
        self.__cov_rcfile = kwargs.get("cov_rcfile", Undefined)
        self.__guess_root = kwargs.get("guess_root", False)
        self.__execution_config = kwargs.get("config", Undefined)

        self.tjignore = ignore
        self.detected_suites = {}
        self.suites = []
        self.requested_suites = suites
        self.__config = Config(config_name=CliConstants.TJ_CONFIG_NAME if
                               self.__execution_config == Undefined else self.__execution_config)
        self.coverage = None
        if self.code_cov:
            import coverage
            if self.cov_rcfile is not None:
                self.coverage = coverage.Coverage(omit="*{sep}test_junkie{sep}*".format(sep=os.sep),
                                                  config_file=self.cov_rcfile)
            else:
                self.coverage = coverage.Coverage(omit="*{sep}test_junkie{sep}*".format(sep=os.sep))
            self.coverage.start()

    @property
    def sources(self):
        if self.__sources == Undefined:
            self.__sources = Config.parse(self.__config.get_value("sources"))
        if self.__sources == Undefined or not isinstance(self.__sources, list):
            raise BadCliParameters("Sources is a required parameter. You can set it in the config via tj config "
                                   "update -s / --sources to persist or pass it in directly to the command you "
                                   "are running via -s / --sources. See documentation: {}"
                                   .format(DocumentationLinks.CLI_RUN))
        return self.__sources

    @property
    def code_cov(self):
        if self.__code_cov == Undefined:
            self.__code_cov = Config.parse(self.__config.get_value("code_cov", default=False))
        return self.__code_cov

    @property
    def cov_rcfile(self):
        if self.__cov_rcfile == Undefined:
            self.__cov_rcfile = Config.parse(self.__config.get_value("cov_rcfile", default=None))
        return self.__cov_rcfile

    @property
    def guess_root(self):
        if self.__guess_root == Undefined:
            # was returned raw, so a saved guess_root=False came back as the (truthy) string "False"
            self.__guess_root = Config.parse(self.__config.get_value("guess_root", default=False))
        return self.__guess_root

    @property
    def execution_config(self):
        if self.__execution_config == Undefined:
            self.__execution_config = Config.get_config_path(CliConstants.TJ_CONFIG_NAME)
        return self.__execution_config

    @staticmethod
    def may_define_suites(source):
        """
        :param source: STRING, contents of a .py file
        :return: BOOLEAN, True if the file looks like it applies the @Suite() decorator (directly, via a module
                 alias like @tj.Suite() or via an import alias like `Suite as S` -> @S()) and is worth importing
        """
        if "test_junkie" not in source:
            return False
        names = ["Suite"] + CliRunner.__REGEX_SUITE_ALIAS.findall(source)
        decorator = r"@\s*(?:[\w.]+\.)?(?:{})\s*\(".format("|".join(re.escape(name) for name in names))
        return re.search(decorator, source) is not None

    def __find_and_register_suite(self, _file_path):

        def raise_import_error(error):

            print("[{status}] There is an import error: {error}"
                  .format(status=CliUtils.format_color_string(value="ERROR", color="red"), error=error))
            print("[{status}] 1. Make sure you have installed all of the packages required for your project "
                  "to work".format(status=CliUtils.format_color_string(value="ERROR", color="red")))
            print("[{status}] 2. Make sure the root of your project is in the PYTHONPATH"
                  .format(status=CliUtils.format_color_string(value="ERROR", color="red")))
            raise

        def guess_project_root(path, _module_name, error):

            print("[{status}] Import error: {error}"
                  .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                          error=error))
            possibility = "{}".format(os.sep).join(path.split(os.sep)[:-1])
            print("[{status}] Trying again with assumption that this is your project root: {assumed_root}"
                  .format(status=CliUtils.format_color_string(value="WARNING", color="yellow"),
                          assumed_root=CliUtils.format_color_string(value=possibility, color="yellow")))
            try:
                sys.path.insert(0, possibility)
                return _load_source(_module_name, _file_path)
            except KeyboardInterrupt:
                print("(Ctrl+C) Exiting!")
                exit(12)
            except ImportError as error:
                if len(possibility.split(os.sep)) > 2:
                    return guess_project_root(possibility, _module_name, error)
                raise_import_error(error)

        module_name = _module_name(_file_path)
        try:
            with suppressed_stdout(suppress=True):
                module = _load_source(module_name, _file_path)
        except ImportError as error:
            if self.guess_root:
                module = guess_project_root(_file_path, module_name, error)
            else:
                raise_import_error(error)
        roster = Builder.get_execution_roster()
        for name, data in list(vars(module).items()):  # definition order, same order the suites will run in
            # only suites defined in this file - a suite imported from elsewhere is picked up from its own file
            if inspect.isclass(data) and data in roster and data.__module__ == module.__name__:
                if not self.requested_suites or name in self.requested_suites:
                    self.suites.append(data)

    def __skip(self, source, directory):

        if source not in directory:
            return True

        for ignored_item in self.tjignore:
            if ignored_item in directory:
                return True
        return False

    def scan(self):

        scanned = set()

        def parse_file(_file):
            path = os.path.normcase(os.path.realpath(_file))
            if path in scanned:  # overlapping sources, e.g. -s tests tests/cli
                return
            scanned.add(path)
            with open(_file, encoding="utf-8") as _doc:
                source = _doc.read()
            if CliRunner.may_define_suites(source):
                self.__find_and_register_suite(_file)

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
                        subdirList.sort()  # walk/glob order is OS-dependent - keep suite order deterministic

                        if self.__skip(source, dirName):
                            continue

                        for file_path in sorted(glob.glob(os.path.join(dirName, "*.py"))):
                            parse_file(file_path)
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

        # unset CLI tag args are Undefined (never None), so Settings falls back to the config for each of them
        tag_config = {"run_on_match_all": args.run_on_match_all,
                      "run_on_match_any": args.run_on_match_any,
                      "skip_on_match_all": args.skip_on_match_all,
                      "skip_on_match_any": args.skip_on_match_any}

        if self.suites:
            print("[{status}] Running tests ...\n"
                  .format(status=CliUtils.format_color_string(value="INFO", color="blue")))
            try:
                runner = Runner(suites=self.suites,
                                html_report=args.html_report,
                                xml_report=args.xml_report,
                                config=self.execution_config)
                runner.run(test_multithreading_limit=args.test_multithreading_limit,
                           suite_multithreading_limit=args.suite_multithreading_limit,
                           tests=args.tests,
                           owners=args.owners,
                           components=args.components,
                           features=args.features,
                           tag_config=tag_config,
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
                if self.coverage is not None:
                    self.coverage.stop()
                    self.coverage.save()
                    import coverage
                    try:
                        print("[{status}] Code coverage report:".format(
                            status=CliUtils.format_color_string(value="INFO", color="blue")))
                        self.coverage.report(show_missing=True, skip_covered=True)
                        print("[{status}] TJ uses Coverage.py. Control it with --cov-rcfile, "
                              "see {link}".format(status=CliUtils.format_color_string(value="TIP", color="blue"),
                                                  link=DocumentationLinks.COVERAGE_CONFIG_FILE))
                    except coverage.misc.CoverageException:
                        CliUtils.print_color_traceback()
                        exit(120)
            report = Aggregator(runner.get_executed_suites()).get_basic_report()["tests"]
            bad = [TestCategory.FAIL, TestCategory.ERROR, TestCategory.IGNORE]
            if any(report.get(s, 0) > 0 for s in bad) or report.get("total", 0) == 0:
                exit(1)
            return
        exit(1)
