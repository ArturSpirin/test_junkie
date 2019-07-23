import ast
from test_junkie.constants import DocumentationLinks, Undefined
from test_junkie.debugger import LogJunkie
from test_junkie.errors import BadParameters
from test_junkie.cli.cli_config import Config


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

    def __init__(self, runner_kwargs, run_kwargs):
        """

        :param runner_kwargs: DICT, arguments that are passed in to initiate the Runner instance
        :param run_kwargs: DICT, arguments that are passes to the run() method of the Runner instance
        """
        runner_kwargs.update(run_kwargs)

        self.kwargs = runner_kwargs

        self.config = None
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
            source = "KWARGS"

        # if value is still __undefined__ and config provided, will check the config for a value to use
        if value is Undefined and self.config is not None:
            source = "DEFAULTS"
            if key in self.config.config.options("runtime"):
                value = self.config.get_value(key)
                if value is not Undefined:
                    try:
                        value = ast.literal_eval(value)
                    except SyntaxError:
                        pass
                    source = "CONFIG @ {}".format(self.config.path)

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
                for prop, value in config.items():
                    if value is Undefined:
                        config.update({prop: self.__get_value(key=prop,
                                                              default=Settings.__DEFAULT_TAGS)})
                self.__tag_config = config
        return self.__tag_config

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
    def html_report(self):
        if self.__html_report is Undefined:
            self.__html_report = self.__get_value(key="html_report",
                                                  default=Settings.__DEFAULT_HTML)
        if self.__html_report and not self.__html_report.endswith(".html"):
            raise BadParameters("\"html_report\" parameter requires full path with a file name and .html extension "
                                "for example: /var/www/html/my_report.html. For more info, see documentation: {link}"
                                .format(link=DocumentationLinks.HTML_REPORT))
        return self.__html_report

    @property
    def xml_report(self):
        if self.__xml_report is Undefined:
            self.__xml_report = self.__get_value(key="xml_report",
                                                 default=Settings.__DEFAULT_XML)
        if self.__xml_report and not self.__xml_report.endswith(".xml"):
            raise BadParameters("\"xml_report\" parameter requires full path with a file name and .html extension "
                                "for example: /var/www/html/my_report.xml. For more info, see documentation: {link}"
                                .format(link=DocumentationLinks.XML_REPORT))
        return self.__xml_report
