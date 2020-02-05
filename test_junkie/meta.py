import threading
import inspect
from test_junkie.decorators import synchronized


def meta(**kwargs):
    return kwargs


class Meta:

    @staticmethod
    @synchronized(threading.Lock())
    def update(suite, parameter=None, suite_parameter=None, **kwargs):

        def __update_test_metadata(class_object):
            for frame in inspect.stack():
                try:
                    getattr(class_object.get_class_object(), str(inspect.getframeinfo(frame[0]).function))
                    test_function_name = str(inspect.getframeinfo(frame[0]).function)
                    for test_object in class_object.get_test_objects():
                        if test_object.get_function_name() == test_function_name:
                            test_object.get_meta(parameter, suite_parameter).update(kwargs)
                            return True
                    return False
                except:
                    pass
            return False

        from test_junkie.builder import Builder
        suite_objects = Builder.get_execution_roster().values()
        for suite_object in suite_objects:
            if suite.__class__ == suite_object.get_class_object():
                if __update_test_metadata(suite_object) is True:
                    return

    @staticmethod
    @synchronized(threading.Lock())
    def get_meta(suite, parameter=None, suite_parameter=None):

        def __get_test_metadata(class_object):
            for frame in inspect.stack():
                try:
                    getattr(class_object.get_class_object(), str(inspect.getframeinfo(frame[0]).function))
                    test_function_name = str(inspect.getframeinfo(frame[0]).function)
                    for test_object in class_object.get_test_objects():
                        if test_object.get_function_name() == test_function_name:
                            return test_object.get_meta(parameter, suite_parameter)
                except:
                    pass

        from test_junkie.builder import Builder
        suite_objects = Builder.get_execution_roster().values()
        for suite_object in suite_objects:
            if suite.__class__ == suite_object.get_class_object():
                metadata = __get_test_metadata(suite_object)
                if metadata is not None:
                    return metadata
