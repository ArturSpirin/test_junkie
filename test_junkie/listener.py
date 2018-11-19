

class Listener:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def on_cancel(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties"))

    def on_success(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties"))

    def on_failure(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_skip(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties"))

    def on_error(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_ignore(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_before_class_error(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_before_class_failure(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_after_class_error(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_after_class_failure(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties", None),
                                          exception=kwargs.get("error", None))

    def on_class_skip(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties"))

    def on_class_cancel(self, **kwargs):
        if kwargs.get("custom_function", None) is not None:
            kwargs.get("custom_function")(properties=kwargs.get("properties"))
