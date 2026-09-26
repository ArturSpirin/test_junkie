from test_junkie.decorators import Suite, test
from tests.junkie_suites.DeepCopyRules import DeepCopyRules


@Suite(rules=DeepCopyRules)
class DeepCopySuite:

    @test(tags=["original"])
    def test_one(self):
        pass
