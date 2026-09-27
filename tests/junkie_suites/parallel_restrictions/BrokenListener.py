from test_junkie.listener import Listener
from test_junkie.decorators import Suite, test


class BrokenListener(Listener):

    def on_success(self, **kwargs):
        raise ValueError("listener is intentionally broken")


@Suite(listener=BrokenListener)
class BrokenListenerSuite:

    @test()
    def a(self):
        pass
