import argparse
import ast
from appdirs import *

from test_junkie.settings import Settings
from test_junkie.cli.cli import CliUtils


if sys.version_info[0] < 3:
    # Python 2
    import ConfigParser as configparser
else:
    # Python 3, module was renamed to configparser
    import configparser


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
monitor_resources=None
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
            self.config = configparser.ConfigParser()
            self.config.read(self.path)
            getattr(self, command)()

    def __set_default_config(self):

        with open(self.path, "w+") as doc:
            doc.write(ConfigManager.__DEFAULTS)
            print("Config restored to default settings!")

    def __restore_value(self, option, value):

        try:
            ast.literal_eval(str(value))
            self.config.set('runtime', option, str(value))
            with open(self.path, 'w+') as doc:
                self.config.write(doc)
            print("[{status}]\t{option}={value}".format(
                status=CliUtils.format_color_string(value="OK", color="green"), option=option, value=value))
        except:
            print("[{status}]\tUnexpected error occurred during update of {setting}={value}"
                  .format(status=CliUtils.format_color_string(value="ERROR", color="red"), setting=option, value=value))
            CliUtils.print_color_traceback()
            exit(120)

    def __print_value(self, option):

        if option in self.config.options("runtime"):
            if sys.version_info[0] < 3:
                # Python 2
                value = self.config.get("runtime", option, Settings.UNDEFINED)
            else:
                # Python 3, module is not backwards compatible and fallback has to be explicitly assigned
                value = self.config.get("runtime", option, fallback=Settings.UNDEFINED)
            if value != Settings.UNDEFINED:
                print("{option}={value}".format(option=option, value=ast.literal_eval(value)))

    def update(self):

        parser = argparse.ArgumentParser(description="Update configuration settings for individual properties",
                                         usage="tj config update [OPTIONS]")
        CliUtils.add_standard_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if not self.args[3:]:
            print("[{status}]\tWhat do you want to update?\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
            exit(0)
        for option, value in args.__dict__.items():
            if value is not Settings.UNDEFINED:
                self.__restore_value(option, value)

    def show(self):

        parser = argparse.ArgumentParser(description='Display current configuration for Test-Junkie',
                                         usage="tj config show [OPTIONS]")
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_boolean_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if args.all or not self.args[3:]:
            print("Config is located at: {}".format(self.path))
            with open(self.path, "r") as cfg:
                print(cfg.read())
            return
        for option, value in args.__dict__.items():
            if value is True:
                self.__print_value(option)

    def restore(self):

        parser = argparse.ArgumentParser(description='Restore config settings to it\'s original values',
                                         usage="tj config restore [OPTIONS]")
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_boolean_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if not self.args[3:]:
            print("[{status}]\tWhat do you want to restore?\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
            return
        if args.all:
            if not os.path.exists(self.root):
                os.makedirs(self.root)
            os.remove(self.path)
            self.__set_default_config()
            return
        for option, value in args.__dict__.items():
            if value is True:
                self.__restore_value(option, None)
