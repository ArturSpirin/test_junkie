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


class DocumentationLinks:

    SUITE_DECORATOR = "https://github.com/ArturSpirin/test_junkie#suite"
    TEST_DECORATOR = "https://github.com/ArturSpirin/test_junkie#test"
    ON_CLASS_IGNORE = "https://github.com/ArturSpirin/test_junkie#on-class-ignore"
    ON_TEST_IGNORE = "https://github.com/ArturSpirin/test_junkie#on-ignore"
    PARAMETERIZED_TESTS = "https://github.com/ArturSpirin/test_junkie#parameterized-tests"
    LISTENERS = "https://github.com/ArturSpirin/test_junkie#test-listeners"
    TAGS = "https://github.com/ArturSpirin/test_junkie#tags"
    SPONSOR_PATREON = "https://www.patreon.com/join/arturspirin"
    RUNNER_OBJECT = "https://github.com/ArturSpirin/test_junkie#runner-object"
    GROUP_RULES = "https://github.com/ArturSpirin/test_junkie#group-rules"
