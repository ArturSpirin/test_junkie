from test_junkie.rules import Rules


class TestRules(Rules):

    def __init__(self, **kwargs):

        Rules.__init__(self, **kwargs)

    def before_class(self):
        # write your code here
        pass

    def before_test(self, **kwargs):
        # write your code here
        pass

    def after_test(self, **kwargs):
        # write your code here
        pass

    def after_class(self):
        # write your code here
        pass
