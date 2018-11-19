import time

from test_junkie.decorators import test, Suite


@Suite(feature="Login", owner="Mike")
class Login:

    @test(component="Authentication", owner="John")
    def positive_login(self):
        time.sleep(1)

    @test(component="Authentication", owner="John")
    def negative_login(self):
        time.sleep(1)

    @test(component="Login Inputs")
    def login_no_password(self):
        time.sleep(1)

    @test(component="Login Inputs")
    def login_no_username(self):
        time.sleep(1)


@Suite(feature="Login", owner="John")
class LoginSessions:

    @test(component="Session Timeout")
    def session_timeout(self):
        time.sleep(1)

    @test(component="Session Timeout")
    def positive_login_on_expired_session(self):
        time.sleep(1)


@Suite(feature="Dashboard", owner="Jane")
class Dashboard:

    @test(component="Charts")
    def add_chart(self):
        time.sleep(1)

    @test(component="Charts")
    def remove_chart(self):
        time.sleep(1)
