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


def test(**decorator_kwargs):
    def decorator(decorated_function):
        def wrapped_function():
            Builder.build_suite_definitions(decorated_function=decorated_function,
                                            decorator_kwargs=decorator_kwargs,
                                            decorator_type=DecoratorType.TEST_CASE)
        return wrapped_function()
    return decorator


def beforeTest(**decorator_kwargs):
    def decorator(decorated_function):
        def wrapped_function():
            Builder.build_suite_definitions(decorated_function=decorated_function,
                                            decorator_kwargs=decorator_kwargs,
                                            decorator_type=DecoratorType.BEFORE_TEST)
        return wrapped_function()
    return decorator


def beforeClass(**decorator_kwargs):
    def decorator(decorated_function):
        def wrapped_function():
            Builder.build_suite_definitions(decorated_function=decorated_function,
                                            decorator_kwargs=decorator_kwargs,
                                            decorator_type=DecoratorType.BEFORE_CLASS)
        return wrapped_function()
    return decorator


def afterTest(**decorator_kwargs):
    def decorator(decorated_function):
        def wrapped_function():
            Builder.build_suite_definitions(decorated_function=decorated_function,
                                            decorator_kwargs=decorator_kwargs,
                                            decorator_type=DecoratorType.AFTER_TEST)
        return wrapped_function()
    return decorator


def afterClass(**decorator_kwargs):
    def decorator(decorated_function):
        def wrapped_function():
            Builder.build_suite_definitions(decorated_function=decorated_function,
                                            decorator_kwargs=decorator_kwargs,
                                            decorator_type=DecoratorType.AFTER_CLASS)
        return wrapped_function()
    return decorator


def synchronized(lock=threading.Lock()):
    def wrapper(f):
        @functools.wraps(f)
        def inner_wrapper(*args, **kw):
            with lock:
                return f(*args, **kw)
        return inner_wrapper
    return wrapper
