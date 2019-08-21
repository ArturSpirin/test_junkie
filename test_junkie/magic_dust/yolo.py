import os
import threading
import traceback


class Yolo:

    __MAP = {}
    __IDENTIFIER = "{0}test_junkie{0}test_junkie{0}runner.py".format(os.sep)

    def __init__(self):
        """
        YOLO: is a context manager (no, not like the contextlib).
        """

    @staticmethod
    def __get_caller(freak_mode=False):
        caller_thread = threading.current_thread()
        caller_function = None
        if freak_mode:  # detect parent function in the stack where the call came from
            in_stack = False
            for line in traceback.format_stack():
                line = line.strip()
                if Yolo.__IDENTIFIER in line:
                    in_stack = True
                if Yolo.__IDENTIFIER not in line and in_stack:
                    caller_function = line.strip()
                    caller_function = caller_function.split("\n")[0].split(" in ")[-1]
                    break
        return caller_thread, caller_function

    @staticmethod
    def get_target(target, freak_mode=False, **kwargs):
        """
        When you call Yolo.get_target() initially, the object created from the target argument gets mapped to the
        thread (or thread/function combo, if you want to get freaky) and then returned, any subsequent calls to Yolo
        to get the same object from the same thread will return the exact same instance of the object. However, if the
        call is made from a different thread, the object will be created again for that specific thread.
        Yolo was created to solve a primary use case for creating Page Objects so that you never have to manage and
        pass the driver instance from Page Object to Page Object. It means that you can just ask for a driver from
        any of the Page Object and be sure that a valid instance of the driver will be returned to you even when
        you are creating many instances of the same page in any of your tests and running them in parallel.
        :param target: Runnable FUNCTION/METHOD. Must returns an instance of an object when executed.
        :param freak_mode: BOOLEAN, enables freak mode which will consider not only which thread the call came from
                           but also the parent function of the stack.
        :param kwargs: Any KWARGS that you want to pass in to your :param target:
        :return: Object created by the :param target:()
        """
        caller_thread, caller_function = Yolo.__get_caller(freak_mode)

        if caller_thread not in Yolo.__MAP:
            Yolo.__MAP.update({caller_thread: {caller_function: {target: target(**kwargs)}}})

        elif caller_function not in Yolo.__MAP[caller_thread]:
            Yolo.__MAP[caller_thread].update({caller_function: {target: target(**kwargs)}})

        elif target not in Yolo.__MAP[caller_thread][caller_function]:
            Yolo.__MAP[caller_thread][caller_function].update({target: target(**kwargs)})

        return Yolo.__MAP[caller_thread][caller_function][target]

    @staticmethod
    def remove_target(target, freak_mode=False):
        """
        Remove any previously mapped target
        :param target: Runnable FUNCTION/METHOD. Must returns an instance of an object when executed.
        :param freak_mode: BOOLEAN, enables freak mode which will consider not only which thread the call came from
                           but also the parent function of the stack.
        :return: BOOLEAN, True/False depending on if the target was removed
        """
        caller_thread, caller_function = Yolo.__get_caller(freak_mode)
        if caller_thread in Yolo.__MAP and \
                caller_function in Yolo.__MAP[caller_thread] and \
                target in Yolo.__MAP[caller_thread][caller_function]:

            Yolo.__MAP[caller_thread][caller_function].pop(target)
            return True

        return False


if "__main__" == __name__:

    def yolo(browser, proxy):
        return browser, proxy

    def func():

        return Yolo.get_target(target=yolo, freak_mode=False, browser=1, proxy=2)

    print(func())
