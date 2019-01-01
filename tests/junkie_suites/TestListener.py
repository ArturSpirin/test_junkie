from test_junkie.listener import Listener


class TestListener(Listener):

    def on_cancel(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_success(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_skip(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_ignore(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_before_class_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_before_class_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_after_class_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_after_class_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"

    def on_class_skip(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_class_cancel(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_class_complete(self, **kwargs):
        assert "properties" in kwargs, "missing properties"

    def on_class_in_progress(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
