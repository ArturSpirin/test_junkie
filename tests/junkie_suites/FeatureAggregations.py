from test_junkie.decorators import test, Suite


@Suite(feature="Login")
class Login:

    @test(component="Authentication")
    def positive_login(self):
        pass

    @test(component="Authentication")
    def negative_login(self):
        pass

    @test(component="Login Inputs")
    def login_no_password(self):
        pass

    @test(component="Login Inputs")
    def login_no_username(self):
        pass


@Suite(feature="Login")
class LoginSessions:

    @test(component="Session Timeout")
    def session_timeout(self):
        pass

    @test(component="Session Timeout")
    def positive_login_on_expired_session(self):
        pass


@Suite(feature="Dashboard")
class Dashboard:

    @test(component="Charts")
    def add_chart(self):
        pass

    @test(component="Charts")
    def remove_chart(self):
        pass
