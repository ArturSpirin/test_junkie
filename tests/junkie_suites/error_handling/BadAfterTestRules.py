from test_junkie.rules import Rules


class BadAfterTestRules(Rules):

    def after_test(self, **kwargs):

        raise Exception("Expected")
