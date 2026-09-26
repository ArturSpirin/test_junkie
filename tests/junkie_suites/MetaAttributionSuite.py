from test_junkie.decorators import Suite, test
from test_junkie.meta import meta, Meta


@Suite()
class MetaAttributionSuite:

    def _update_via_helper(self):
        # Meta.update() called from a helper, not straight from the test - the stack walk
        # has to skip past this frame to find the real test
        Meta.update(self, name="updated via helper")

    @test(meta=meta(name="original"))
    def test_one(self):
        self._update_via_helper()
