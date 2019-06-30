import argparse
import ast
from appdirs import *
from test_junkie.settings import Settings
from test_junkie.cli.cli import CliUtils


class ConfigManager:
    """
    only use for cli, do not use for parsing the config when running tests
    """
    __CONFIG_NAME = "tj.cfg"
    __DEFAULTS = """
[runtime]
test_multithreading_limit=None
suite_multithreading_limit=None
html_report=None
xml_report=None
monitor_resources=None
tests=None
features=None
components=None
owners=None
run_on_match_all=None
run_on_match_any=None
skip_on_match_all=None
skip_on_match_any=None
sources=None
"""

    def __init__(self, command=None, args=None):

        self.path = ConfigManager.get_config_path()
        self.args = args

        if command is not None and args is not None:
            if not os.path.exists(self.path):
                self.restore(new=True)
            self.config = ConfigManager.get_config_parser(self.path)
            getattr(self, command)()

    @staticmethod
    def get_root_dir():
        return user_data_dir("Test-Junkie")

    @staticmethod
    def get_config_path():
        return "{root}{sep}{name}".format(root=ConfigManager.get_root_dir(),
                                          name=ConfigManager.__CONFIG_NAME,
                                          sep=os.sep)

    @staticmethod
    def get_config_parser(path):
        if sys.version_info[0] < 3:
            # Python 2
            import ConfigParser as configparser
        else:
            # Python 3, module was renamed to configparser
            import configparser
        config = configparser.ConfigParser()
        config.read(path)
        return config

    def __set_default_config(self):

        with open(self.path, "w+") as doc:
            doc.write(ConfigManager.__DEFAULTS)
            print("[{status}] Config restored to default settings!"
                  .format(status=CliUtils.format_color_string(value="OK", color="green")))

    def __restore_value(self, option, value):

        try:
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
            value = ConfigManager.get_value(self.config, option)
            if value != Settings.UNDEFINED:
                print("{option}={value}".format(option=option, value=ast.literal_eval(value)))

    @staticmethod
    def get_value(config, option):

        if sys.version_info[0] < 3:
            # Python 2
            value = config.get("runtime", option, Settings.UNDEFINED)
        else:
            # Python 3, module is not backwards compatible and fallback has to be explicitly assigned
            value = config.get("runtime", option, fallback=Settings.UNDEFINED)
        return value

    def update(self):

        parser = argparse.ArgumentParser(description="Update configuration settings for individual properties",
                                         usage="tj config update [OPTIONS]")
        CliUtils.add_standard_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if not self.args[3:]:
            print("[{status}]\tWhat do you want to update?\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
            return
        for option, value in args.__dict__.items():
            if value is not Settings.UNDEFINED:
                self.__restore_value(option, value)
        print("[{status}]\tRestore original value with tj config restore [OPTION]. tj config restore -h for more info."
              .format(status=CliUtils.format_color_string(value="TIP", color="blue")))

    def show(self):

        parser = argparse.ArgumentParser(description='Display current configuration for Test-Junkie',
                                         usage="tj config show [OPTIONS]")
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_boolean_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if args.all or not self.args[3:]:
            print("Config is located at: {path}\n"
                  .format(path=CliUtils.format_color_string(value=self.path, color="green")))
            with open(self.path, "r") as cfg:
                print(cfg.read())
            return
        for option, value in args.__dict__.items():
            if value is True:
                self.__print_value(option)

    def restore(self, new=False):

        parser = argparse.ArgumentParser(description='Restore config settings to it\'s original values',
                                         usage="tj config restore [OPTIONS]")
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_boolean_tj_args(parser)
        args = parser.parse_args(self.args[3:])
        if args.all or new:
            if not os.path.exists(ConfigManager.get_root_dir()):
                os.makedirs(ConfigManager.get_root_dir())
            if os.path.exists(self.path):
                os.remove(self.path)
            self.__set_default_config()
            return
        if not self.args[3:]:
            print("[{status}]\tWhat do you want to restore?\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
            return
        for option, value in args.__dict__.items():
            if value is True:
                self.__restore_value(option, None)
