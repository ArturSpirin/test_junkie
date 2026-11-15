import functools
import threading

from test_junkie.builder import Builder
from test_junkie.constants import DecoratorType


class Suite(object):

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, cls):

        Builder.build_suite_definitions(decorated_function=cls,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.TEST_SUITE)
        return cls


class test(object):

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.build_suite_definitions(decorated_function=decorated_function,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.TEST_CASE)
        return decorated_function


class beforeTest(object):
    """
    Runs before every test. If it fails, the test is recorded as an error and @afterTest does not run for it,
    so release anything it set up before failing yourself
    """

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.build_suite_definitions(decorated_function=decorated_function,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.BEFORE_TEST)
        return decorated_function


class beforeClass(object):

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.build_suite_definitions(decorated_function=decorated_function,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.BEFORE_CLASS)
        return decorated_function


class afterTest(object):
    """
    Runs after every test that got past @beforeTest: one that passed, failed, was skipped at runtime with skip()
    or was cancelled mid-run. It does not run after a failed @beforeTest
    """

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.build_suite_definitions(decorated_function=decorated_function,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.AFTER_TEST)
        return decorated_function


class afterClass(object):

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.build_suite_definitions(decorated_function=decorated_function,
                                        decorator_kwargs=self.decorator_kwargs,
                                        decorator_type=DecoratorType.AFTER_CLASS)
        return decorated_function


class GroupRules(object):

    def __init__(self, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs

    def __call__(self, decorated_function):

        Builder.register_group_rules(decorated_function=decorated_function,
                                     decorator_kwargs=self.decorator_kwargs,
                                     decorator_type=DecoratorType.GROUP_RULES)
        return decorated_function


class afterGroup(object):

    def __init__(self, group, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs
        self.group = group

    def __call__(self, decorated_function):

        Builder.add_group_rule(suites=self.group,
                               decorated_function=decorated_function,
                               decorator_kwargs=self.decorator_kwargs,
                               decorator_type=DecoratorType.AFTER_GROUP)
        return decorated_function


class beforeGroup(object):

    def __init__(self, group, **decorator_kwargs):
        self.decorator_kwargs = decorator_kwargs
        self.group = group

    def __call__(self, decorated_function):

        Builder.add_group_rule(suites=self.group,
                               decorated_function=decorated_function,
                               decorator_kwargs=self.decorator_kwargs,
                               decorator_type=DecoratorType.BEFORE_GROUP)
        return decorated_function


def synchronized(lock=threading.Lock()):
    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kw):
            with lock:
                return f(*args, **kw)
        return inner_wrapper
    return wrapper
