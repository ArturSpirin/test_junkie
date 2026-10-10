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
from test_junkie.meta import Meta
from test_junkie.retry import RetryPolicy, When

def _screenshot():
    """A small drawn 'browser screenshot' of a dashboard with a broken widget (Pillow), else a 1x1 PNG"""
    try:
        import io
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                             "1f15c4890000000d49444154789c63f80f00000101000518d84e0000000049454e44ae426082")
    font = ImageFont.load_default(size=13)
    small = ImageFont.load_default(size=11)
    image = Image.new("RGB", (640, 380), "#f4f5f7")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 640, 34], fill="#1f2430")
    draw.text((14, 10), "Acme Analytics  ·  Dashboard", fill="#ffffff", font=font)
    draw.rectangle([0, 34, 120, 380], fill="#e6e8ec")
    for i, item in enumerate(["Overview", "Reports", "Widgets", "Settings"]):
        draw.text((14, 52 + i * 26), item, fill="#2b2f38" if item != "Widgets" else "#e8660a", font=font)
    cards = [(136, 50, 372, 200, "Revenue", "$48,210"), (388, 50, 624, 200, "Active users", "1,284"),
             (136, 216, 372, 366, "Conversion", "3.4%")]
    for x0, y0, x1, y1, title, value in cards:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=8, fill="#ffffff", outline="#d9dce2")
        draw.text((x0 + 14, y0 + 12), title, fill="#6b7280", font=small)
        draw.text((x0 + 14, y0 + 34), value, fill="#111827", font=ImageFont.load_default(size=24))
        draw.line([(x0 + 14, y1 - 30), (x0 + 80, y1 - 52), (x0 + 140, y1 - 40), (x1 - 14, y1 - 70)],
                  fill="#f37814", width=3)
    draw.rounded_rectangle([388, 216, 624, 366], radius=8, fill="#fff5f5", outline="#e5484d", width=2)
    draw.text((402, 230), "Chart widget", fill="#6b7280", font=small)
    draw.text((402, 280), "Error: widget could not be removed", fill="#c62828", font=font)
    draw.text((402, 300), "'NoneType' object has no attribute 'delete'", fill="#c62828", font=small)
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


SCREENSHOT = _screenshot()
ATTEMPTS = {}


def attempt(key):
    ATTEMPTS[key] = ATTEMPTS.get(key, 0) + 1
    return ATTEMPTS[key]


class PaymentsSandbox(RetryPolicy):
    """Retry what the payments sandbox throws at us, never a wrong answer."""
    when = [When(ConnectionError, attempts=3, delay=0.2),
            When(message="503", attempts=2, delay=0.3, backoff=2)]
    circuit = 5


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
        Meta.attach("dashboard.png", SCREENSHOT)
        Meta.link("Bug DASH-311", "https://example.com/browse/DASH-311")
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


@Suite(feature="API", owner="Eve", tags=["api"])
class EnvironmentSuite:

    @test(component="Health Check", tags=["api", "smoke"],
          parameters=[{"env": "staging"}, {"env": "production"}, {"env": "dev"}])
    def check_health(self, parameter):
        time.sleep(0.06)
        if parameter["env"] == "production":
            raise AssertionError("Health check failed: production returned 503")

    @test(component="Config", tags=["api"],
          parameters=[{"format": "json"}, {"format": "yaml"}, {"format": "toml"}])
    def load_config(self, parameter):
        time.sleep(0.04)
        if parameter["format"] == "toml":
            raise Exception("TOML parser not available in this environment")


@Suite(feature="Checkout", owner="Grace", tags=["api", "payments"], retry_policy=PaymentsSandbox)
class CheckoutApiSuite:

    @test(component="Payments", tags=["smoke"], parameters=["visa", "amex"],
          meta={"name": "Charge a card", "expected": "201 Created"})
    def charges_card(self, parameter):
        time.sleep(0.05)
        run = attempt(("charges_card", parameter))
        Meta.update(card=parameter, order_id="ord_{}_{}".format(parameter, 1042))
        Meta.append("steps", "POST /v1/charges (attempt {})".format(run))
        if parameter == "visa" and run == 1:
            raise ConnectionError("Connection reset by payments sandbox")  # passes on the retry: flaky

    @test(component="Payments", tags=["regression"])
    def refunds_order(self):
        time.sleep(0.06)
        run = attempt("refunds_order")
        Meta.update(order_id="ord_visa_1042", refund_id="re_7781")
        Meta.link("Order in admin", "https://example.com/admin/orders/ord_visa_1042")
        Meta.attach("refund_response.json", b'{"id": "re_7781", "status": "pending", "amount": 4999}')
        if run == 1:
            raise AssertionError("Gateway returned 503 Service Unavailable")  # retried by message, then passes

    @test(component="Payments", tags=["regression"])
    def rejects_expired_card(self):
        time.sleep(0.04)
        Meta.update(card="4000000000000069", expected_error="card_expired")
        raise AssertionError("Expected 402 card_expired, got 200")  # a wrong answer: never retried


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
        suites=[LoginSuite, LogoutSuite, DashboardSuite, ReportSuite, ApiSuite,
                EnvironmentSuite, CheckoutApiSuite, NotificationSuite],
        monitor_resources=True,
        html_report=out,
    )
    runner.run()
    print("Report written to:", out)
