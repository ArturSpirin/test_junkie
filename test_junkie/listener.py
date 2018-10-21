import traceback


class Listener:

    def __init__(self, **kwargs):
        from test_junkie.debugger import LogJunkie
        self.logger = LogJunkie
        self.kwargs = kwargs

    def on_in_progress(self, properties):

        self.logger.debug("===========Test In Progress===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("=================================")

    def on_cancel(self, properties):

        self.logger.debug("===========Test Canceled===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("=================================")

    def on_success(self, properties):
        self.logger.debug("===========Test passed===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("=================================")

    def on_failure(self, properties, exception):
        self.logger.debug("===========Test failed===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("=================================")

    def on_skip(self, properties):
        self.logger.debug("===========Test skipped==========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("=================================")

    def on_error(self, properties, exception):
        self.logger.debug("===========Test error===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        # self.logger.debug(exception.with_traceback(exception.__traceback__))
        self.logger.debug("=================================")

    def on_ignore(self, properties, exception):
        self.logger.debug("===========Test ignored==========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("=================================")

    def on_before_class_error(self, properties, exception):
        self.logger.debug("===========Before Class Error===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("========================================")

    def on_before_class_failure(self, properties, exception):
        self.logger.debug("===========Before Class Failed===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("=========================================")

    def on_after_class_error(self, properties, exception):
        self.logger.debug("===========After Class Error===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("=======================================")

    def on_after_class_failure(self, properties, exception):
        self.logger.debug("===========After Class Failed===========")
        self.logger.debug("Properties: {}".format(properties))
        traceback.print_exc()
        # traceback.print_tb(exception.__traceback__)
        self.logger.debug("========================================")

    def on_class_in_progress(self, properties):
        self.logger.debug("===========Class In Progress===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("===================================")

    def on_class_skip(self, properties):
        self.logger.debug("===========Class Skipped===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("===================================")

    def on_class_cancel(self, properties):
        self.logger.debug("===========Class Canceled===========")
        self.logger.debug("Properties: {}".format(properties))
        self.logger.debug("===================================")
