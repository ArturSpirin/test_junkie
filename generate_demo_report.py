"""
Generate a rich demo HTML report for testjunkie_web.
Run from the test_junkie repo root:
  python generate_demo_report.py
"""
import sys
import time

sys.path.insert(0, __file__.replace("generate_demo_report.py", ""))

from test_junkie.runner import Runner
from test_junkie.decorators import Suite, test, beforeClass, afterClass, beforeTest, afterTest


@Suite(feature="Authentication", owner="Alice", tags=["smoke"])
class LoginSuite:

    @beforeClass()
    def setup(self):
        time.sleep(0.05)

    @afterClass()
    def teardown(self):
        time.sleep(0.03)

    @beforeTest()
    def before_each(self):
        pass

    @afterTest()
    def after_each(self):
        pass

    @test(component="Credentials", owner="Alice", tags=["smoke", "regression"])
    def valid_credentials(self):
        time.sleep(0.15)

    @test(component="Credentials", tags=["regression"])
    def invalid_password(self):
        time.sleep(0.08)
        raise AssertionError("Expected 401, got 200")

    @test(component="2FA", owner="Bob", tags=["smoke"])
    def two_factor_prompt(self):
        time.sleep(0.12)

    @test(component="2FA", owner="Bob")
    def two_factor_invalid_code(self):
        time.sleep(0.09)
        raise AssertionError("OTP code not rejected")

    @test(component="Session", tags=["regression"])
    def session_expiry(self):
        time.sleep(0.14)


@Suite(feature="Authentication", owner="Bob")
class LogoutSuite:

    @test(component="Session", tags=["smoke"])
    def clean_logout(self):
        time.sleep(0.07)

    @test(component="Session", tags=["regression"])
    def logout_clears_cookies(self):
        time.sleep(0.06)


@Suite(feature="Dashboard", owner="Carol", tags=["ui"])
class DashboardSuite:

    @beforeClass()
    def setup(self):
        time.sleep(0.04)

    @afterClass()
    def teardown(self):
        time.sleep(0.04)

    @beforeTest()
    def before_each(self):
        pass

    @afterTest()
    def after_each(self):
        pass

    @test(component="Widgets", owner="Carol", tags=["ui", "smoke"])
    def load_widgets(self):
        time.sleep(0.2)

    @test(component="Widgets", tags=["ui"])
    def add_chart_widget(self):
        time.sleep(0.11)

    @test(component="Widgets", tags=["ui"])
    def remove_widget(self):
        time.sleep(0.09)
        raise Exception("AttributeError: 'NoneType' object has no attribute 'delete'")

    @test(component="Filters", owner="Dave", tags=["ui", "regression"])
    def apply_date_filter(self):
        time.sleep(0.13)

    @test(component="Filters", owner="Dave", tags=["regression"])
    def apply_status_filter(self):
        time.sleep(0.08)

    @test(component="Filters", owner="Dave")
    def clear_all_filters(self):
        time.sleep(0.07)

    @test(component="Export", tags=["ui"])
    def export_csv(self):
        time.sleep(0.16)

    @test(component="Export")
    def export_pdf(self):
        time.sleep(0.19)
        raise AssertionError("PDF export produced empty file")


@Suite(feature="Reporting", owner="Dave", tags=["reporting"])
class ReportSuite:

    @test(component="HTML Report", tags=["smoke", "reporting"])
    def generate_html(self):
        time.sleep(0.1)

    @test(component="HTML Report", tags=["reporting"])
    def html_includes_all_tests(self):
        time.sleep(0.09)

    @test(component="XML Report", tags=["reporting"])
    def generate_xml(self):
        time.sleep(0.07)

    @test(component="XML Report", owner="Eve", tags=["reporting"])
    def xml_schema_valid(self):
        time.sleep(0.08)

    @test(component="Metrics", owner="Eve", tags=["reporting"])
    def avg_runtime_accuracy(self):
        time.sleep(0.06)


@Suite(feature="API", owner="Eve")
class ApiSuite:

    @test(component="REST", tags=["api", "smoke"])
    def get_tests_endpoint(self):
        time.sleep(0.05)

    @test(component="REST", tags=["api"])
    def post_run_endpoint(self):
        time.sleep(0.06)

    @test(component="REST", tags=["api"])
    def delete_run_endpoint(self):
        time.sleep(0.04)

    @test(component="Auth Headers", tags=["api", "security"])
    def missing_auth_header(self):
        time.sleep(0.03)
        raise AssertionError("Expected 403, got 500")

    @test(component="Auth Headers", tags=["api", "security"])
    def expired_token(self):
        time.sleep(0.04)

    @test(component="Rate Limiting", tags=["api"])
    def rate_limit_enforced(self):
        time.sleep(0.05)


@Suite(feature="Notifications", owner="Alice", tags=["notifications"])
class NotificationSuite:

    @test(component="Email", owner="Frank", tags=["notifications"])
    def send_email_on_fail(self):
        time.sleep(0.07)

    @test(component="Email", owner="Frank", tags=["notifications"])
    def email_template_renders(self):
        time.sleep(0.08)

    @test(component="Slack", tags=["notifications"])
    def slack_webhook_fires(self):
        time.sleep(0.06)

    @test(component="Slack", tags=["notifications"])
    def slack_message_format(self):
        time.sleep(0.05)
        raise Exception("ConnectionError: Failed to connect to Slack webhook")


if __name__ == "__main__":
    out = "demo_report.html"
    runner = Runner(
        suites=[LoginSuite, LogoutSuite, DashboardSuite, ReportSuite, ApiSuite, NotificationSuite],
        monitor_resources=True,
        html_report=out,
    )
    runner.run()
    print("Report written to:", out)
