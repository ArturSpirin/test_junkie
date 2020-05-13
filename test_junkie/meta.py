import threading
import inspect
from test_junkie.decorators import synchronized


def meta(**kwargs):
    """
    Use this function in order to define metadata for a @test().
    aka @test(meta=meta(name="Example Name", expected="...", ...))
    :param kwargs: key/value pairs
    :return: Dictionary
    """
    return kwargs


class Meta:

    @staticmethod
    @synchronized(threading.Lock())
    def update(suite, parameter=None, suite_parameter=None, **kwargs):
        """
        Use this function inside a @test() where you want to update properties of the metadata
        :param suite: Object, class object that the test is part of. Typically will be "self".
        :param parameter: User defined parameter for the test.
        :param suite_parameter: User defined suite parameter for the test.
        :param kwargs: Dictionary aka {"actual_result": "3 new accounts created, 0 failed", "...": ..., ...}
        :return: None
        """
        metadata = Meta.get_meta(suite, parameter, suite_parameter)
        if metadata is not None:
            metadata.update(kwargs)

    @staticmethod
    @synchronized(threading.Lock())
    def get_meta(suite, parameter=None, suite_parameter=None):
        """
        Use this function inside a @test() where you want to check the current values of the metadata for that test
        :param suite: Object, class object that the test is part of. Typically will be "self".
        :param parameter: User defined parameter for the test.
        :param suite_parameter: User defined suite parameter for the test.
        :return: Dictionary
        """
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
