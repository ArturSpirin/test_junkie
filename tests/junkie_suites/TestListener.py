from test_junkie.listener import Listener


class TestListener(Listener):

    def __init__(self, **kwargs):
        Listener.__init__(self, **kwargs)

    def on_cancel(self, properties):
        pass

    def on_success(self, properties):
        pass

    def on_failure(self, properties, exception):
        pass

    def on_skip(self, properties):
        pass

    def on_error(self, properties, exception):
        pass

    def on_ignore(self, properties, exception):
        pass

    def on_before_class_error(self, properties, exception):
        pass

    def on_before_class_failure(self, properties, exception):
        pass

    def on_after_class_error(self, properties, exception):
        pass

    def on_after_class_failure(self, properties, exception):
        pass

    def on_class_skip(self, properties):
        pass

    def on_class_cancel(self, properties):
        pass
