import time

from test_junkie.decorators import test, Suite, afterClass, afterTest, beforeTest, beforeClass


@Suite(feature="Login", owner="Mike")
class Login:

    @test(component="Authentication", owner="John", tags=["awesome", "tags"])
    def positive_login(self):
        time.sleep(1)

    @test(component="Authentication", owner="John")
    def negative_login(self):
        time.sleep(1)

    @test(component="Login Inputs", tags=["awesome", "tags"])
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

    @test(component="Session Timeout", tags=["awesome", "tags"])
    def positive_login_on_expired_session(self):
        time.sleep(1)


@Suite(feature="Dashboard", owner="Jane", retry=3)
class Dashboard:

    @beforeClass()
    def before_class(self):
        time.sleep(1)

    @beforeTest()
    def before_test(self):
        pass

    @afterTest()
    def after_test(self):
        pass

    @afterClass()
    def after_class(self):
        time.sleep(1)

    @test(component="Charts")
    def add_chart(self):
        time.sleep(1)

    @test(component="Charts", tags=["awesome", "tags"])
    def remove_chart(self):
        time.sleep(1)

    @test(component="Charts", tags=["awesome", "tags"])
    def remove_chart(self):
        time.sleep(1)
        raise Exception("Test")

    @test(component="Charts", tags=["awesome", "tags"])
    def remove_chart(self):
        time.sleep(1)
        raise AssertionError("Test")
