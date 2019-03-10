from test_junkie.rules import Rules


class BadBeforeTestRules(Rules):

    def before_test(self, **kwargs):

        raise Exception("Expected")
