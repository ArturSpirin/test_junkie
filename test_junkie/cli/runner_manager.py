import imp
import inspect
import os
import pprint
import time
import re
from setuptools.glob import glob

from test_junkie.cli.config_manager import ConfigManager
from test_junkie.runner import Runner


class RunnerManager:

    __REGEX_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite as.*?\n"
    __REGEX_NO_ALIAS_IMPORT = ".*?from test_junkie.decorators import(.*?)Suite.*?\n"

    def __init__(self, root, ignore):

        self.root = root
        self.tjignore = ignore
        self.detected_suites = {}
        self.suites = []

    def __find_and_register_suite(self, _suite_alias, _source, _file_path):

        def load_module(_item):
            if "\nclass " in _item:
                decorated_class = item.split("\nclass ")[-1].strip()
                module_name = os.path.splitext(os.path.basename(_file_path))[0]
                module = imp.load_source(module_name, _file_path)
                for name, data in inspect.getmembers(module):
                    if name == decorated_class and inspect.isclass(data):
                        self.suites.append(data)

        matches = re.findall("@{alias}((.|\n)*?):".format(alias=_suite_alias), _source)
        for match in matches:
            if isinstance(match, tuple):
                for item in match:
                    load_module(item)
            else:
                load_module(match)

    def __skip(self, directory):

        if self.root not in directory:
            print("{} is not part of the root directory!".format(directory))
            return True

        for ignored_item in self.tjignore:
            if ignored_item in directory:
                print("{} is ignored!".format(directory))
                return True
        return False

    def scan(self):

        start = time.time()
        for dirName, subdirList, fileList in os.walk(self.root, topdown=True):

            if self.__skip(dirName):
                continue

            for file_path in glob(os.path.join(os.path.dirname(dirName+"\\"), "*.py")):
                with open(file_path) as doc:
                    source = doc.read()

                    suite_imported_as_alias = re.findall(RunnerManager.__REGEX_ALIAS_IMPORT, source)
                    if suite_imported_as_alias:
                        suite_alias = suite_imported_as_alias[-1].split("Suite")[-1].split("as")[-1].split(",")[0].strip()
                        self.__find_and_register_suite(suite_alias, source, file_path)
                        continue

                    suite_imported = re.findall(RunnerManager.__REGEX_NO_ALIAS_IMPORT, source)
                    if suite_imported:
                        self.__find_and_register_suite("Suite", source, file_path)
                        continue

        pprint.pprint(self.suites)
        print("Finished in: {} seconds. Found: {} suites.".format(time.time() - start, len(self.suites)))

    def run_suites(self, args):

        if self.suites:
            runner = Runner(suites=self.suites,
                            html=args.html,
                            xml=args.xml,
                            config=ConfigManager().path)
            runner.run(test_multithreading_limit=args.test_multithreading_limit,
                       suite_multithreading_limit=args.suite_multithreading_limit,
                       owners=args.owners,
                       components=args.components,
                       features=args.features,
                       tag_config={"run_on_match_all": args.run_on_match_all,
                                   "run_on_match_any": args.run_on_match_any,
                                   "skip_on_match_all": args.skip_on_match_all,
                                   "skip_on_match_any": args.skip_on_match_any})
        else:
            print "No test suites found in: ", self.root
