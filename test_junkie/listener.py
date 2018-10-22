import traceback


class Listener:

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def on_in_progress(self, properties):
        pass

    def on_cancel(self, properties):
        pass

    def on_success(self, properties):
        pass

    def on_failure(self, properties, exception):
        traceback.print_exc()

    def on_skip(self, properties):
        pass

    def on_error(self, properties, exception):
        traceback.print_exc()

    def on_ignore(self, properties, exception):
        traceback.print_exc()

    def on_before_class_error(self, properties, exception):
        traceback.print_exc()

    def on_before_class_failure(self, properties, exception):
        traceback.print_exc()

    def on_after_class_error(self, properties, exception):
        traceback.print_exc()

    def on_after_class_failure(self, properties, exception):
        traceback.print_exc()

    def on_class_in_progress(self, properties):
        pass

    def on_class_skip(self, properties):
        pass

    def on_class_cancel(self, properties):
        pass
