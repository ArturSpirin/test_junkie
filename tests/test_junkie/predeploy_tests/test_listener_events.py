from test_junkie.decorators import Suite, test
from tests.junkie_suites import ListenerEventSuites


@Suite()
class ListenerEventsSuite:

    @test()
    def group_failure_and_cancel_events(self):
        ListenerEventSuites.run_checks()
