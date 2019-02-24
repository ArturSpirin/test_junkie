

class Listener(object):

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @staticmethod
    def __process_event(**kwargs):
        if kwargs.get("custom_function", None) is not None:
            if kwargs.get("error", None) is None:
                kwargs.get("custom_function")(properties=kwargs.get("properties"))
            else:
                kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                              exception=kwargs.get("error", None),
                                              trace=kwargs.get("trace", None))

    def on_cancel(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_success(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_failure(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_skip(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_error(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_ignore(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_in_progress(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_complete(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_before_class_error(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_before_class_failure(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_after_class_error(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_after_class_failure(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_class_skip(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_class_cancel(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_class_in_progress(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_class_complete(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_class_ignore(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_before_group_failure(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_before_group_error(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_after_group_failure(self, **kwargs):
        Listener.__process_event(**kwargs)

    def on_after_group_error(self, **kwargs):
        Listener.__process_event(**kwargs)
