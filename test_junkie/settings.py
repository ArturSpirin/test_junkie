import os

from test_junkie.constants import DocumentationLinks, Undefined
from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters, ConfigError
from test_junkie.cli.cli_config import Config
from test_junkie.rerun import Rerun


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
    __DEFAULT_QUIET = False
    __DEFAULT_PER_TEST = False
    __DEFAULT_CAPTURE = True

    def __init__(self, runner_kwargs, run_kwargs):
        """

        :param runner_kwargs: DICT, arguments that are passed in to initiate the Runner instance
        :param run_kwargs: DICT, arguments that are passes to the run() method of the Runner instance
        """
        # merged into a copy - updating runner_kwargs in place leaked one run()'s arguments into the next
        self.kwargs = dict(runner_kwargs)
        self.kwargs.update(run_kwargs)

        self.config = None
        self.from_config = {}  # setting -> value, for the settings this run took from the saved config
        if self.kwargs.get("config", None) is not None:
            self.config = Config(config_name=self.kwargs["config"])

        self.__tag_config = Undefined
        self.__test_thread_limit = Undefined
        self.__suite_thread_limit = Undefined
        self.__features = Undefined
        self.__components = Undefined
        self.__owners = Undefined
        self.__tests = Undefined
        self.__resources_mon = Undefined
        self.__html_report = Undefined
        self.__xml_report = Undefined
        self.__quiet = Undefined
        self.__per_test = Undefined
        self.__capture = Undefined
        self.__json_report = Undefined
        self.__retry = Undefined
        self.__retry_policy = Undefined
        self.__rerun = Undefined

        self.__print_settings()

    def __print_settings(self):

        LogJunkie.debug("============= Runtime Settings =============")
        LogJunkie.debug("Test Thread Limit: {value}:({type})".format(value=self.test_thread_limit,
                                                                    type=type(self.test_thread_limit)))
        LogJunkie.debug("Suite Thread Limit: {value}".format(value=self.suite_thread_limit))
        LogJunkie.debug("Features: {value}".format(value=self.features))
        LogJunkie.debug("Components: {value}".format(value=self.components))
        LogJunkie.debug("Owners: {value}".format(value=self.owners))
        LogJunkie.debug("Tests: {value}".format(value=self.tests))
        LogJunkie.debug("Tags: {value}".format(value=self.tags))
        LogJunkie.debug("Monitor Resources: {value}".format(value=self.monitor_resources))
        LogJunkie.debug("HTML Report: {value}:({type})".format(value=self.html_report, type=type(self.html_report)))
        LogJunkie.debug("XML Report: {value}:({type})".format(value=self.xml_report, type=type(self.xml_report)))
        LogJunkie.debug("Quiet: {value}:({type})".format(value=self.quiet, type=type(self.quiet)))
        LogJunkie.debug("============================================")

    def __get_value(self, key, default):
        """
        Generic method to resolve value to be used during runtime for a particular setting/property.
        1. Attempt to retrieve value from the explicitly passed in kwargs during Runner initiation
        2. If value is still __undefined__, attempt to retrieve value from the config __IF__ config was provided to
           the Runner during the initiation
        3. If value is still __undefined__, will use default values
        :param key: STRING, property key aka features, owners, test_multithreading_limit etc
        :param default: DATA VALUE, value to default to aka None, False, True, 1 etc
        :return: DATA VALUE
        """
        value = Undefined  # we start with __undefined__, because None is a valid value
        source = "DEFAULTS"

        # if we have kwargs, attempt to retrieve value for the key
        if self.kwargs is not None:
            value = self.kwargs.get(key, Undefined)
            if value is not Undefined:
                source = "KWARGS"

        # if value is still __undefined__ and config provided, will check the config for a value to use
        if value is Undefined and self.config is not None:
            source = "DEFAULTS"
            if key in self.config.config.options("runtime"):
                value = self.config.get_value(key)
                if value is not Undefined:
                    value = Config.parse(value)
                    source = "CONFIG @ {}".format(self.config.path)
                    if value is not None:
                        self.from_config[key] = value

        LogJunkie.debug("Setting: {setting} Source: {source}".format(setting=key, source=source))
        # if value is still __undefined__, will return default value
        return value if value is not Undefined else default

    @property
    def test_thread_limit(self):

        if self.__test_thread_limit is Undefined:
            self.__test_thread_limit = self.__get_value(key="test_multithreading_limit",
                                                        default=Settings.__DEFAULT_TEST_THREAD_LIMIT)
        return self.__test_thread_limit

    @property
    def suite_thread_limit(self):

        if self.__suite_thread_limit is Undefined:
            self.__suite_thread_limit = self.__get_value(key="suite_multithreading_limit",
                                                         default=Settings.__DEFAULT_SUITE_THREAD_LIMIT)
        return self.__suite_thread_limit

    @property
    def features(self):

        if self.__features is Undefined:
            self.__features = self.__get_value(key="features",
                                               default=Settings.__DEFAULT_FEATURES)
        return self.__features

    @property
    def components(self):

        if self.__components is Undefined:
            self.__components = self.__get_value(key="components",
                                                 default=Settings.__DEFAULT_COMPONENTS)
        return self.__components

    @property
    def owners(self):

        if self.__owners is Undefined:
            self.__owners = self.__get_value(key="owners",
                                             default=Settings.__DEFAULT_OWNERS)
        return self.__owners

    @property
    def tests(self):
        if self.__tests is Undefined:
            self.__tests = self.__get_value(key="tests",
                                            default=Settings.__DEFAULT_TESTS)
        return self.__tests

    @property
    def tags(self):
        if self.__tag_config == Undefined:
            config = self.kwargs.get("tag_config", Undefined)
            if config is Undefined:
                config = {}
                properties = ["run_on_match_all", "run_on_match_any", "skip_on_match_all", "skip_on_match_any"]
                for prop in properties:
                    config.update({prop: self.__get_value(key=prop,
                                                          default=Settings.__DEFAULT_TAGS)})
                self.__tag_config = config
            else:
                Settings.__validate_tag_config_type(config)  # before .items() - a list used to raise AttributeError
                for prop, value in config.items():
                    if value is Undefined:
                        config.update({prop: self.__get_value(key=prop,
                                                              default=Settings.__DEFAULT_TAGS)})
                self.__tag_config = config
            Settings.__validate_tag_config(self.__tag_config)
        return self.__tag_config

    @staticmethod
    def __validate_tag_config_type(config):
        if not isinstance(config, dict):
            raise ConfigError("`tag_config` must be a dict, got {}. See documentation: {}"
                              .format(type(config).__name__, DocumentationLinks.TAGS))

    @staticmethod
    def __validate_tag_config(config):
        # a bad value used to surface as a bare TypeError from deep inside the suite filters
        Settings.__validate_tag_config_type(config)
        for prop, value in config.items():
            if value is not None and value is not Undefined and \
                    not (isinstance(value, (list, tuple)) and all(isinstance(tag, str) for tag in value)):
                raise ConfigError("`tag_config` value for \"{}\" must be a list of tag strings, got: {!r}. "
                                  "See documentation: {}".format(prop, value, DocumentationLinks.TAGS))

    @property
    def monitor_resources(self):
        if self.__resources_mon is Undefined:
            self.__resources_mon = self.__get_value(key="monitor_resources",
                                                    default=Settings.__DEFAULT_RESOURCE_MON)
        return self.__resources_mon

    @property
    def quiet(self):
        if self.__quiet is Undefined:
            self.__quiet = self.__get_value(key="quiet",
                                            default=Settings.__DEFAULT_QUIET)
        return self.__quiet

    @property
    def per_test(self):
        if self.__per_test is Undefined:
            self.__per_test = self.__get_value(key="per_test", default=Settings.__DEFAULT_PER_TEST)
        return self.__per_test

    @property
    def capture(self):
        """
        False shows what tests print and log live instead of only for the ones that didn't pass (tj run --no-capture)
        """
        if self.__capture is Undefined:
            self.__capture = self.__get_value(key="capture", default=Undefined)
            if self.__capture is Undefined:  # tj config update --no-capture saves it as no_capture
                no_capture = self.__get_value(key="no_capture", default=None)
                self.__capture = Settings.__DEFAULT_CAPTURE if no_capture is None else not no_capture
        return self.__capture

    def __report(self, key, extension, link):
        """
        A report path: a file with the right extension, or a folder (then report.<extension> in it)
        """
        path = self.__get_value(key=key, default=None)
        if not path:
            return None
        path = str(path)
        if os.path.isdir(path) or path.endswith(("/", "\\")):
            return os.path.join(path, "report" + extension)
        if not path.endswith(extension):
            raise BadParameters("\"{key}\" needs a {ext} file or a folder, for example: reports/run{ext} or reports/. "
                                "Got: {path}. For more info, see documentation: {link}"
                                .format(key=key, ext=extension, path=path, link=link))
        return path

    @property
    def html_report(self):
        if self.__html_report is Undefined:
            self.__html_report = self.__report("html_report", ".html", DocumentationLinks.HTML_REPORT)
        return self.__html_report

    @property
    def json_report(self):
        if self.__json_report is Undefined:
            self.__json_report = self.__report("json_report", ".json", DocumentationLinks.DOMAIN)
        return self.__json_report

    @property
    def retry(self):
        """
        :return: INT, how many times a test may run (tj run --retry N, 1 for --no-retry), or None to keep each test's
        """
        if self.__retry is Undefined:
            if self.__get_value(key="no_retry", default=None):
                self.__retry = 1
            else:
                value = self.__get_value(key="retry", default=None)
                if value is not None and (not isinstance(value, int) or value < 1):
                    raise BadParameters("\"retry\" needs a whole number of 1 or more, got: {!r}".format(value))
                self.__retry = value
        return self.__retry

    @property
    def retry_policy(self):
        """
        :return: RetryPolicy for every test that sets no retry of its own and whose suite sets no retry_policy
                 (tj run --retry-policy module:Class, Runner.run(retry_policy=...)), or None
        """
        if self.__retry_policy is Undefined:
            from test_junkie.retry import load, resolve
            value = self.__get_value(key="retry_policy", default=None)
            self.__retry_policy = load(value) if isinstance(value, str) else resolve(value, "retry_policy")
        return self.__retry_policy

    @property
    def rerun(self):
        """
        :return: Rerun, the tests to run again (tj run --rerun FILE), or None to run everything
        """
        if self.__rerun is Undefined:
            value = self.__get_value(key="rerun", default=None)
            if isinstance(value, (str, os.PathLike)):
                value = Rerun.from_report(value)
            elif value is not None and not isinstance(value, Rerun):
                raise BadParameters("\"rerun\" needs a Rerun or the path to a JSON report, got: {!r}. "
                                    "See documentation: {}".format(value, DocumentationLinks.RERUN))
            self.__rerun = value
        return self.__rerun

    @property
    def limits(self):
        """
        :return: DICT, the Limiter settings this run sets (Runner.run() kwargs, tj run flags or the saved config),
                 e.g. {"test_throttling": 1}. What isn't set keeps the value Limiter has in code
        """
        from test_junkie.objects import Limiter
        limits = {}
        for setting in Limiter.SETTINGS:
            value = self.__get_value(key=setting, default=None)
            if value is not None:
                limits[setting] = value
        return limits

    @property
    def xml_report(self):
        if self.__xml_report is Undefined:
            self.__xml_report = self.__report("xml_report", ".xml", DocumentationLinks.XML_REPORT)
        return self.__xml_report
