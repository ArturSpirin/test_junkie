import ConfigParser
import ast


class Settings:

    __DEFAULT_TEST_THREAD_LIMIT = 1
    __DEFAULT_SUITE_THREAD_LIMIT = 1
    __DEFAULT_COMPONENTS = None
    __DEFAULT_FEATURES = None
    __DEFAULT_OWNERS = None
    __DEFAULT_TAGS = None
    __DEFAULT_HTML = None
    __DEFAULT_XML = None
    __DEFAULT_TESTS = None
    __DEFAULT_RESOURCE_MON = False
    UNDEFINED = "__undefined__"

    def __init__(self, kwargs):

        self.kwargs = kwargs
        self.config = None
        if kwargs.get("config", None) is not None:
            self.config = ConfigParser.ConfigParser()
            self.config.read(kwargs.get("config"))

    def __get_value(self, key, default):
        """
        Generic method to resolve value to be used during runtime for a particular setting/property.
        1. Attempt to retrieve value from the explicitly passed in kwargs during Runner initiation
        2. If value is still __undefined__, attempt to retrieve value from the config if config was provided to
           the Runner during the initiation
        3. If value is still __undefined__, will use default values
        :param key: STRING, property key aka features, owners, test_multithreading_limit etc
        :param default: DATA VALUE, value to default to aka None, False, True, 1 etc
        :return: DATA VALUE
        """
        value = Settings.UNDEFINED  # we start with __undefined__, because None is a valid value

        # if we have kwargs, attempt to retrieve value for the key
        if self.kwargs is not None:
            value = self.kwargs.get(key, Settings.UNDEFINED)

        # if value is still __undefined__ and config provided, will check the config for a value to use
        if value == Settings.UNDEFINED and self.config is not None:
            if key in self.config.options("runtime"):
                value = self.config.get("runtime", key, Settings.UNDEFINED)
                if value != Settings.UNDEFINED:
                    value = ast.literal_eval(value)
        # if value != Settings.UNDEFINED:
        #     print "Key: {} Default: {} Value: {} Type: {}".format(key, default, value, type(value))
        # if value is still __undefined__, will return default value
        return value if value != Settings.UNDEFINED else default

    @property
    def test_thread_limit(self):
        return self.__get_value(key="test_multithreading_limit", default=Settings.__DEFAULT_TEST_THREAD_LIMIT)

    @property
    def suite_thread_limit(self):
        return self.__get_value(key="suite_multithreading_limit", default=Settings.__DEFAULT_SUITE_THREAD_LIMIT)

    @property
    def features(self):
        return self.__get_value(key="features", default=Settings.__DEFAULT_FEATURES)

    @property
    def components(self):
        return self.__get_value(key="components", default=Settings.__DEFAULT_COMPONENTS)

    @property
    def owners(self):
        return self.__get_value(key="owners", default=Settings.__DEFAULT_OWNERS)

    @property
    def tests(self):
        return self.__get_value(key="tests", default=Settings.__DEFAULT_TESTS)

    @property
    def tags(self):
        tag_config = {"run_on_match_all": self.__get_value(key="run_on_match_all", default=Settings.__DEFAULT_TAGS),
                      "run_on_match_any": self.__get_value(key="run_on_match_any", default=Settings.__DEFAULT_TAGS),
                      "skip_on_match_all": self.__get_value(key="skip_on_match_all", default=Settings.__DEFAULT_TAGS),
                      "skip_on_match_any": self.__get_value(key="skip_on_match_any", default=Settings.__DEFAULT_TAGS)}
        return tag_config

