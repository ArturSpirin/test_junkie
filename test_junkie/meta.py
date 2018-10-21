import threading
from test_junkie.decorators import synchronized


def meta(**kwargs):
    return kwargs


class Meta:

    def __init__(self):

        pass

    @staticmethod
    @synchronized(threading.Lock())
    def update(parameter=None, suite_parameter=None, **kwargs):
        from test_junkie.builder import Builder
        suites = Builder.get_execution_roster().values()
        for suite in suites:
            if suite.update_test_meta(parameter, suite_parameter, **kwargs) is True:
                return
