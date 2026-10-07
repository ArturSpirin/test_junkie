import argparse
import ast
import os
import re
from appdirs import user_data_dir

from test_junkie.constants import CliConstants, Undefined


class _CliUtils(object):
    """
    Loads test_junkie.cli.cli (and colorama) on first use - Config is imported by every run, the CLI parts aren't
    """
    def __getattr__(self, name):
        from test_junkie.cli.cli import CliUtils as utils
        return getattr(utils, name)


CliUtils = _CliUtils()


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

    @staticmethod
    def parse(value):
        """
        Values are saved with repr() and read back as Python literals. Configs written by older versions saved
        plain strings unquoted (e.g. html_report=report.html) - those come back as the string itself.
        :param value: STRING value as stored in the config
        :return: DATA VALUE
        """
        if not isinstance(value, str):
            return value
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    def set_value(self, option, value):

        self.config.set('runtime', option, repr(value))
        with open(self.path, 'w+') as doc:
            self.config.write(doc)

    def get_value(self, option, default=Undefined):
        section = "runtime"
        try:
            return self.config.get(section, option, fallback=default)
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
        :return: STRING, root directory for TJ to store its configs and other assets.
                 $TEST_JUNKIE_HOME if set, otherwise the per-user app data dir
        """
        return os.environ.get(CliConstants.HOME_ENV_VAR) or user_data_dir("Test-Junkie")

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
        import configparser
        # no %-interpolation: a "%" in a value (e.g. a report path) made saving and reading fail
        config = configparser.ConfigParser(interpolation=None)
        config.read(self.path)
        return config


# what tj config show groups settings by, and the value each one has when it isn't saved (None: no default)
_GROUPS = [
    ("Discovery", [("sources", None), ("guess_root", "off")]),
    ("Parallel", [("test_multithreading_limit", "1"), ("suite_multithreading_limit", "1")]),
    ("Filters", [("tests", None), ("features", None), ("components", None), ("owners", None),
                 ("run_on_match_any", None), ("run_on_match_all", None), ("skip_on_match_any", None),
                 ("skip_on_match_all", None)]),
    ("Reports and output", [("html_report", None), ("xml_report", None), ("monitor_resources", "off"),
                            ("code_cov", "off"), ("cov_rcfile", None), ("quiet", "off"), ("per_test", "off"),
                            ("no_capture", "off")]),
]
_DEFAULTS = dict(item for _, items in _GROUPS for item in items)
_WIDTH = 30


class _Parser(argparse.ArgumentParser):
    """
    Bad option values get the same ERROR line as everything else in tj config, and exit 120 instead of 2
    """

    def error(self, message):
        console = CliConfig.console()
        match = re.match(r"argument (\S+): invalid int value: '(.*)'", message)
        if match:
            message = "{} needs a whole number, got \"{}\".".format(match.group(1).replace("/", " / "), match.group(2))
        else:
            message = message[0].upper() + message[1:] + "."
        console.emit(["{}  {}".format(console.badge("ERROR", "err"), message),
                      "         " + console.style("Nothing was saved. {} -h lists every option.".format(self.prog), "dim")])
        exit(120)


class CliConfig:
    """
    only use for cli, do not use for parsing the config when running tests
    """

    def __init__(self, config_name, command, args):

        self.args = args
        self.config = Config(config_name=config_name)
        self.__console = CliConfig.console()
        getattr(self, command)()

    @staticmethod
    def console():
        from test_junkie.console import Console
        return Console(None, mode="report")

    @staticmethod
    def format_value(value):
        """
        :return: STRING, a saved value as tj config prints it, None if it isn't set
        """
        if value is None or value is Undefined:
            return None
        if isinstance(value, bool):
            return "on" if value else "off"
        if isinstance(value, (list, tuple)):
            return ", ".join(str(item) for item in value)
        return str(value)

    def __current(self, option):
        if option not in self.config.config.options("runtime"):
            return None
        return CliConfig.format_value(Config.parse(self.config.get_value(option)))

    def __unset(self, option):
        default = _DEFAULTS.get(option)
        style = self.__console.style
        return style("·", "dim") + ("  " + style("default {}".format(default), "dim") if default else "")

    def __error(self, message, hint):
        console = self.__console
        console.emit(["{}  {}".format(console.badge("ERROR", "err"), message), "         " + console.style(hint, "dim")])
        exit(120)

    def __save(self, option, value):

        try:
            self.config.set_value(option, value)
        except Exception:
            console = self.__console
            console.emit(["{}  Unexpected error occurred during update of {}={}".format(
                console.badge("ERROR", "err"), option, value)])
            CliUtils.print_color_traceback()
            exit(120)

    @staticmethod
    def __flags(parser):
        """
        :return: DICT of option -> the shortest flag for it, e.g. test_multithreading_limit -> -T
        """
        return {action.dest: min(action.option_strings, key=len) for action in parser._actions if action.option_strings}

    def update(self):

        parser = _Parser(description="Update configuration settings for individual properties",
                         usage="tj config update [OPTIONS]", prog="tj config update")
        CliUtils.add_standard_tj_args(parser)
        if not self.args[3:]:
            self.__error("Nothing to update. Pass the settings to save, e.g. {}".format(
                self.__console.style("tj config update -s tests -T 4", "bold")), "tj config update -h lists every setting.")
        args = parser.parse_args(self.args[3:])
        flags = CliConfig.__flags(parser)
        changes = []
        for option, value in args.__dict__.items():
            if value is not Undefined:
                changes.append((option, self.__current(option), value))
                self.__save(option, value)
        console, style = self.__console, self.__console.style
        dot = style(" · ", "dim")
        lines = ["{}  {} setting{}{}{}".format(console.badge("SAVED", "pass"), len(changes),
                                               "" if len(changes) == 1 else "s", dot, style(self.config.path, "dim"))]
        for option, old, new in changes:
            lines.append("  {}{}  →  {}".format(option.ljust(_WIDTH), old if old is not None else style("·", "dim"),
                                                style(CliConfig.format_value(new), "bold")))
        lines.extend(["", style("  Undo: tj config restore {}".format(" ".join(flags[o] for o, _, _ in changes)), "dim")])
        console.emit(lines)

    def show(self):

        parser = _Parser(description='Display current configuration for Test-Junkie', usage="tj config show [OPTIONS]",
                         prog="tj config show")
        parser.add_argument("-a", "--all", action="store_true", default=False, help="Show every setting")
        CliUtils.add_standard_boolean_tj_args(parser)
        if not self.args[3:]:
            style = self.__console.style
            self.__error("Which settings? e.g. {}, or {}".format(style("tj config show -s -T", "bold"),
                                                                   style("tj config show --all", "bold")),
                         "tj config show -h lists every setting.")
        args = parser.parse_args(self.args[3:])
        console, style = self.__console, self.__console.style
        dot = style(" · ", "dim")

        def row(option):
            value = self.__current(option)
            return "  " + option.ljust(_WIDTH) + (style(value, "bold") if value is not None else self.__unset(option))

        if args.all:
            lines = ["{}  {}".format(style("Config", "bold"), self.config.path), ""]
            saved = 0
            for group, items in _GROUPS:
                lines.append(style(group, "bold"))
                for option, _ in items:
                    lines.append(row(option))
                    saved += self.__current(option) is not None
                lines.append("")
            total = sum(len(items) for _, items in _GROUPS)
            lines.extend([style("─" * 80, "dim"), "",
                          "{} of {} settings saved{}{}".format(saved, total, dot, style(
                              "tj config update -h to change one, tj config restore -h to clear one", "dim"))])
            console.emit(lines)
            return
        console.emit([row(option) for option, value in args.__dict__.items() if value is True])

    def restore(self):

        parser = _Parser(description='Restore config settings to it\'s original values', usage="tj config restore [OPTIONS]",
                         prog="tj config restore")
        parser.add_argument("-a", "--all", action="store_true", default=False,
                            help="Will restore all config settings to its default values")
        CliUtils.add_standard_boolean_tj_args(parser)
        if not self.args[3:]:
            style = self.__console.style
            self.__error("Nothing to restore. e.g. {}, or {}".format(style("tj config restore -T", "bold"),
                                                                       style("tj config restore --all", "bold")),
                         "tj config restore -h lists every setting.")
        args = parser.parse_args(self.args[3:])
        console, style = self.__console, self.__console.style
        dot = style(" · ", "dim")
        options = [option for _, items in _GROUPS for option, _ in items]
        if args.all:
            before = [(option, self.__current(option)) for option in options]
            self.config.restore()
            had = [(option, value) for option, value in before if value is not None]
            lines = ["{}  all {} settings to their defaults{}{} had values".format(
                console.badge("RESTORED", "skip"), len(options), dot, len(had))]
        else:
            restored = [option for option, value in args.__dict__.items() if value is True]
            had = [(option, self.__current(option)) for option in restored]
            for option in restored:
                self.__save(option, None)
            lines = ["{}  {} setting{} to {} default{}".format(
                console.badge("RESTORED", "skip"), len(restored), "" if len(restored) == 1 else "s",
                "its" if len(restored) == 1 else "their", "" if len(restored) == 1 else "s")]
        for option, old in had:
            if old is None and args.all:
                continue
            default = _DEFAULTS.get(option)
            lines.append("  {}{}  →  {}".format(option.ljust(_WIDTH), old if old is not None else style("·", "dim"),
                                                style("default {}".format(default) if default else "·", "dim")))
        console.emit(lines)
