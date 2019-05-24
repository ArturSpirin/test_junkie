import ConfigParser
import argparse
import ast
import traceback

from appdirs import *

from test_junkie.cli.cli import CliUtils
from test_junkie.constants import DocumentationLinks


class ConfigManager:
    """
    only use for cli, do not use for parsing the config when running tests
    """

    __DEFAULTS = """
[runtime]
test_multithreading_limit=1
suite_multithreading_limit=1
html=None
xml=None
monitor_ resources=False
features=None
components=None
owners=None
run_on_match_all=None
run_on_match_any=None
skip_on_match_all=None
skip_on_match_any=None
artifacts=None
source=None
root=None
"""

    def __init__(self, command=None, args=None):

        self.root = user_data_dir("Test-Junkie")
        self.config_name = "tj.cfg"
        self.path = "{root}{sep}{name}".format(root=self.root, name=self.config_name, sep=os.sep)
        self.args = args

        if command is not None and args is not None:
            if not os.path.exists(self.path):
                self.restore()

            getattr(self, command)()

    def __set_default_config(self):

        with open(self.path, "w+") as cfg:
            cfg.write(ConfigManager.__DEFAULTS)
        print("Restored!")

    def update(self):
        # TODO May want to generalize addition of certain update & run args with extensive help
        #      text that would apply to both areas

        parser = argparse.ArgumentParser(description="Update configuration settings for individual properties",
                                         usage="tj config update [OPTIONS]")

        parser.add_argument("-T", "--test_multithreading_limit", type=int, default=None,
                            help="Will allocated N number of threads and enable test level multi threading")

        parser.add_argument("-S", "--suite_multithreading_limit", type=int, default=None,
                            help="Will allocated N number of threads and enable suite level multi threading")

        parser.add_argument("--html", type=str, default=None,
                            help="Will set path to FILE or DIRECTORY where to save HTML report after test execution")

        parser.add_argument("--xml", type=str, default=None,
                            help="Will set path to FILE or DIRECTORY where to save XML report after test execution")

        parser.add_argument("-s", "--source", type=str, default=None, help="Will set path to source")
        parser.add_argument("-f", "--features", nargs="+", default=None, help="Will set features list")
        parser.add_argument("-c", "--components", nargs="+", default=None, help="Will set components list")
        parser.add_argument("-o", "--owners", nargs="+", default=None, help="Will set owners list")

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
        args = parser.parse_args(self.args[3:])
        if not self.args[3:]:
            print("What do you want to update?\n")
            parser.print_help()
            exit(0)

        config = ConfigParser.ConfigParser()
        config.read(self.path)

        for option, value in args.__dict__.items():
            if value:
                try:
                    ast.literal_eval(str(value))
                    config.set('runtime', option, str(value))
                    print("{}\t{}\t[OK]".format(option, value))
                except:
                    print("Make sure value: {} is valid Python datatype. "
                          "It must pass ast.literal_eval()\t[ERROR]\n".format(value))
                    print(traceback.format_exc())
                    exit(120)
        with open(self.path, 'wb') as doc:
            config.write(doc)

    def show(self):
        argparse.ArgumentParser(description='Display current configuration for Test-Junkie')
        print("Config is located at: {}".format(self.path))
        with open(self.path, "r") as cfg:
            print(cfg.read())

    def restore(self):
        # TODO add all of the options that can be restored so you can do
        #      tj config restore -k : to restore tag config for example
        parser = argparse.ArgumentParser(description='Restore config settings to it\'s original values')
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if not self.args[3:]:
            print("What do you want to update?\n")
            parser.print_help()
            exit(0)
        if args.all:
            if not os.path.exists(self.root):
                os.makedirs(self.root)
            os.remove(self.path)
            self.__set_default_config()
