from tests.junkie_suites import ListenerEventSuites


def test_group_failure_and_cancel_events():
    ListenerEventSuites.run_checks()
