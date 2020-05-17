from appdirs import *
from test_junkie.constants import CliConstants, Undefined
from rich import print


class Config:

    def __init__(self, config_name):

        if config_name not in [CliConstants.TJ_CONFIG_NAME]:
            if not os.path.exists(config_name):
                print(f"[[[bold red]ERROR[/bold red]]]\tNot able to find config @ "
                      "[bold red]{config_name}[/bold red]. Please check that the file exists.")
                exit(120)
            self.path = config_name
        else:
            self.path = f"{Config.get_root_dir()}{os.sep}{config_name}"
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
            value = self.config.get(section, option, fallback=default)
            return value
        except Exception:
            print(f"[[[bold red]ERROR[bold red]]]\tPlease check config: [bold red]{self.path}[/bold red] "
                  "it appears that its miss-configured.")
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
    def get_agents_root_dir():
        """
        :return: STRING, root directory for TJ HQ Agents
        """
        return f"{Config.get_root_dir()}{os.sep}agents"

    @staticmethod
    def get_hq_root_dir():
        """
        :return: STRING, root directory for HQ Servers
        """
        return f"{Config.get_root_dir()}{os.sep}hq"

    @staticmethod
    def get_config_path(config_name):
        """
        :param config_name: STRING, name of the config that you want to get the path for
        :return: STRING, path to the requested config
        """
        return "{root}{sep}{name}".format(root=Config.get_root_dir(), name=config_name, sep=os.sep)

    def __get_parser(self):
        """
        :return: ConfigParser object
        """
        import configparser
        config = configparser.ConfigParser()
        config.read(self.path)
        return config
