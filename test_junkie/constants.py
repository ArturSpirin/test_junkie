

class TestCategory:

    SUCCESS = "success"
    FAIL = "fail"
    IGNORE = "ignore"
    ERROR = "error"
    SKIP = "skip"
    CANCEL = "cancel"
    ALL = [SUCCESS, FAIL, IGNORE, ERROR, SKIP, CANCEL]
    ALL_UN_SUCCESSFUL = [FAIL, IGNORE, ERROR]


class SuiteCategory:

    SUCCESS = "success"
    FAIL = "fail"
    SKIP = "skip"
    CANCEL = "cancel"
    IGNORE = "ignore"
    ALL = [SUCCESS, FAIL, SKIP, CANCEL, IGNORE]
    ALL_UN_SUCCESSFUL = [FAIL, IGNORE]

    """
    This status means something failed outside of Test Junkie,
    like custom event listener function was missing required arguments in the signature.
    This status is used as fallback and is not set by Test Junkie during test execution.
    Tests that error out, suite should be marked with the FAIL status.
    Thus, this status is not part of the ALL nor ALL_UN_SUCCESSFUL list and should stay that way
    """
    ERROR = "error"


class DecoratorType:

    TEST_SUITE = "testSuite"
    BEFORE_CLASS = "beforeClass"
    BEFORE_TEST = "beforeTest"
    AFTER_TEST = "afterTest"
    AFTER_CLASS = "afterClass"
    TEST_CASE = "testCase"
    GROUP_RULES = "groupRules"
    BEFORE_GROUP = "beforeGroup"
    AFTER_GROUP = "afterGroup"


class Event:

    ON_SUCCESS = 1
    ON_FAILURE = 2
    ON_ERROR = 3
    ON_SKIP = 4
    ON_IGNORE = 5
    ON_CANCEL = 6
    ON_CLASS_SKIP = 7
    ON_CLASS_CANCEL = 8
    ON_BEFORE_CLASS_ERROR = 9
    ON_BEFORE_CLASS_FAIL = 10
    ON_AFTER_CLASS_ERROR = 11
    ON_AFTER_CLASS_FAIL = 12
    ON_CLASS_IN_PROGRESS = 13
    ON_CLASS_COMPLETE = 14
    ON_CLASS_IGNORE = 15
    ON_BEFORE_GROUP_FAIL = 16
    ON_BEFORE_GROUP_ERROR = 17
    ON_AFTER_GROUP_FAIL = 18
    ON_AFTER_GROUP_ERROR = 19
    ON_IN_PROGRESS = 20
    ON_COMPLETE = 21


class DocumentationLinks:

    __DOMAIN = "https://www.test-junkie.com"
    SUITE_DECORATOR = "{}/documentation/#suite".format(__DOMAIN)
    TEST_DECORATOR = "{}/documentation/#test".format(__DOMAIN)
    ON_CLASS_IGNORE = "{}/documentation/#on_class_ignore".format(__DOMAIN)
    ON_TEST_IGNORE = "{}/documentation/#on_ignore".format(__DOMAIN)
    PARAMETERIZED_TESTS = "{}/documentation/#parameters".format(__DOMAIN)
    LISTENERS = "{}/documentation/#listeners".format(__DOMAIN)
    TAGS = "{}/documentation/#tags".format(__DOMAIN)
    RUNNER_OBJECT = "{}/documentation/#runner".format(__DOMAIN)
    GROUP_RULES = "{}/documentation/#GroupRules".format(__DOMAIN)
    THREADING = "{}/documentation/#parallel_execution".format(__DOMAIN)
    HTML_REPORT = "{}/documentation/#html_report".format(__DOMAIN)
    XML_REPORT = "{}/documentation/#xml_report".format(__DOMAIN)
    RETRY = "{}/documentation/#retry".format(__DOMAIN)
    FEATURES = "{}/documentation/#features".format(__DOMAIN)
    COMPONENTS = "{}/documentation/#components".format(__DOMAIN)
    ASSIGNEES = "{}/documentation/#assignees".format(__DOMAIN)


class Color:

    SUCCESS = "#12d479"
    FAIL = "#fcd75f"
    ERROR = "#ff7651"
    IGNORE = "#cce4eb"
    SKIP = "#34bff5"
    CANCEL = "#f19def"

    MAPPING = {TestCategory.SUCCESS: SUCCESS,
               TestCategory.FAIL: FAIL,
               TestCategory.ERROR: ERROR,
               TestCategory.IGNORE: IGNORE,
               TestCategory.SKIP: SKIP,
               TestCategory.CANCEL: CANCEL}
