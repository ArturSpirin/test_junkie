from test_junkie.rules import Rules


class DeepCopyRules(Rules):
    # mutates the suite/test it's handed, so tests can check the live objects stay untouched

    def __init__(self, **kwargs):
        Rules.__init__(self, **kwargs)

    def before_class(self):
        self.kwargs["suite"].get_kwargs()["mutated_by_rule"] = True

    def before_test(self, **kwargs):
        kwargs["test"].get_tags().append("mutated_by_rule")
