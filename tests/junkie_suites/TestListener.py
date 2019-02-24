from test_junkie.listener import Listener


class TestListener(Listener):

    def on_cancel(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_success(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_skip(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_ignore(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_in_progress(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_complete(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "test_meta" in kwargs["properties"], "missing test meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jto" in kwargs["properties"]["jm"], "missing test object in junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_before_class_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_before_class_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_after_class_error(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_after_class_failure(self, **kwargs):
        assert "exception" in kwargs, "missing exception object"
        assert "trace" in kwargs, "missing traceback"
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_class_skip(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_class_cancel(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_class_complete(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta"
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_class_in_progress(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_class_ignore(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_before_group_failure(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_before_group_error(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_after_group_failure(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"

    def on_after_group_error(self, **kwargs):
        assert "properties" in kwargs, "missing properties"
        assert "suite_meta" in kwargs["properties"], "missing suite meta"
        assert "jm" in kwargs["properties"], "missing test junkie meta: {}".format(kwargs)
        assert "jso" in kwargs["properties"]["jm"], "missing suite object in junkie meta"
