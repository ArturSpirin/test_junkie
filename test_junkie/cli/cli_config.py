import argparse
import ast
from appdirs import *

from test_junkie.constants import CliConstants, Undefined
from test_junkie.cli.cli import CliUtils


class Config:

    def __init__(self, config_name):

        if config_name not in [CliConstants.TJ_CONFIG_NAME]:
            if not os.path.exists(config_name):
                print("[{status}]\tWasn't able to find config @ {path}. Please check that the file exists."
                      .format(status=CliUtils.format_color_string(value="ERROR", color="red"),
                              path=CliUtils.format_color_string(value=config_name, color="red")))
                exit(120)
            self.path = config_name
        else:
            self.path = "{root}{sep}{file}".format(root=Config.get_root_dir(), file=config_name, sep=os.sep)
        if not os.path.exists(Config.get_root_dir()):
            os.makedirs(Config.get_root_dir())
        if not os.path.exists(self.path):
            self.restore()
        self.config = self.__get_parser()

    def remove(self):
        """
        Will remove config from file storage
        :return: None
        """
        if os.path.exists(self.path):
            os.remove(self.path)

    def restore(self, data=None):
        """
        Overrides the config with provided data or defaults
        :param data: STRING, Optional data to put in the config
        :return: None
        """
        self.remove()
        with open(self.path, "w+") as doc:
            doc.write(data if data else CliConstants.DEFAULTS)

    def set_value(self, option, value):

        self.config.set('runtime', option, str(value))
        with open(self.path, 'w+') as doc:
            self.config.write(doc)

    def get_value(self, option, default=Undefined):
        section = "runtime"
        try:
            if sys.version_info[0] < 3:
                # Python 2
                value = self.config.get(section, option, default)
            else:
                # Python 3, module is not backwards compatible and fallback has to be explicitly assigned
                value = self.config.get(section, option, fallback=default)
            return value
        except Exception:
            print("[{status}]\tPlease check config: {path} it appears that its miss-configured."
                  .format(status=CliUtils.format_color_string(value="ERROR", color="red"),
                          path=CliUtils.format_color_string(value=self.path, color="red")))
            raise

    def read(self):

        with open(self.path, 'r') as doc:
            return doc.read()

    @staticmethod
    def get_root_dir():
        """
        :return: STRING, root directory for TJ to store its configs and other assets
        """
        return user_data_dir("Test-Junkie")

    @staticmethod
    def get_config_path(config_name):
        """
        :param config_name: STRING, name of the config that you want to get the path for
        :return: STRING, path to the requested config
        """
        return "{root}{sep}{name}".format(root=Config.get_root_dir(), name=config_name, sep=os.sep)

    def __get_parser(self):
        """
        :param path: STRING, path to the config file
        :return: ConfigParser object
        """
        if sys.version_info[0] < 3:
            # Python 2
            import ConfigParser as configparser
        else:
            # Python 3, module was renamed to configparser
            import configparser
        config = configparser.ConfigParser()
        config.read(self.path)
        return config


class CliConfig:
    """
    only use for cli, do not use for parsing the config when running tests
    """

    def __init__(self, config_name, command, args):

        self.args = args
        self.config = Config(config_name=config_name)
        getattr(self, command)()

    def __restore_value(self, option, value):

        try:
            self.config.set_value(option, value)
            print("[{status}]\t{option}={value}".format(
                status=CliUtils.format_color_string(value="OK", color="green"), option=option, value=value))
        except:
            print("[{status}]\tUnexpected error occurred during update of {setting}={value}"
                  .format(status=CliUtils.format_color_string(value="ERROR", color="red"), setting=option, value=value))
            CliUtils.print_color_traceback()
            exit(120)

    def __print_value(self, option):

        if option in self.config.config.options("runtime"):
            value = self.config.get_value(option)
            if value != Undefined:
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
            return
        for option, value in args.__dict__.items():
            if value is not Undefined:
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
                  .format(path=CliUtils.format_color_string(value=self.config.path, color="green")))
            with open(self.config.path, "r") as cfg:
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
        if args.all:
            self.config.restore()
            print("[{status}] Config restored to default settings!"
                  .format(status=CliUtils.format_color_string(value="OK", color="green")))
            return
        if not self.args[3:]:
            print("[{status}]\tWhat do you want to restore?\n".format(
                status=CliUtils.format_color_string(value="ERROR", color="red")))
            parser.print_help()
            return
        for option, value in args.__dict__.items():
            if value is True:
                self.__restore_value(option, None)
