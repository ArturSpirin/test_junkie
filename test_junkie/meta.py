import threading
from test_junkie.decorators import synchronized


def meta(**kwargs):
    return kwargs


class Meta:

    @staticmethod
    @synchronized(threading.Lock())
    def update(suite, parameter=None, suite_parameter=None, **kwargs):
        from test_junkie.builder import Builder
        suite_objects = Builder.get_execution_roster().values()
        for suite_object in suite_objects:
            if suite.__class__ == suite_object.get_class_object().__class__:
                if suite_object._update_test_meta(parameter, suite_parameter, **kwargs) is True:
                    return

    @staticmethod
    @synchronized(threading.Lock())
    def get_meta(suite, parameter=None, suite_parameter=None):
        from test_junkie.builder import Builder
        suite_objects = Builder.get_execution_roster().values()
        for suite_object in suite_objects:
            if suite.__class__ == suite_object.get_class_object().__class__:
                m = suite_object._get_test_meta(parameter, suite_parameter)
                if m is not None:
                    return m
