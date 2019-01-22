
class Rules:

    def __init__(self, **kwargs):

        self.kwargs = kwargs

    def before_class(self):
        pass

    def before_test(self, **kwargs):
        pass

    def after_test(self, **kwargs):
        pass

    def after_class(self):
        pass
