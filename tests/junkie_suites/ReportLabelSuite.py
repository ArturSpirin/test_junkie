"""
A suite whose results exercise the HTML report's Fail/Error labels and its escaping of user-provided values.
Shared by the pytest and TJ test paths.
"""
import json
import os
import re
import tempfile

from test_junkie.decorators import Suite, test


@Suite(owner="<i>owner</i>")
class ReportLabelSuite:

    @test(tags=["<b>tag</b>"])
    def real_assertion(self):
        assert 1 == 2

    @test()
    def error_mentioning_assertion(self):
        # an Error, not a Fail - the report used to label it Fail because the text contains "AssertionError"
        raise ValueError("expected an AssertionError here")


def _embedded(html, name):
    return json.loads(re.search(r"const {} = (.*?);\n".format(name), html).group(1))


def run_checks():
    from test_junkie.runner import Runner
    path = os.path.join(tempfile.mkdtemp(), "report.html")
    Runner([ReportLabelSuite], quiet=True, html_report=path).run()
    with open(path, encoding="utf-8") as doc:
        html = doc.read()

    tests = {entry["test"]: entry["id"] for entry in _embedded(html, "TESTS")}
    details = _embedded(html, "DETAILS")

    def first_attempt_status(test_name):
        return details[str(tests[test_name])]["variants"][0]["attempts"][0]["test"]["status"]

    assert first_attempt_status("real_assertion") == "Fail"
    assert first_attempt_status("error_mentioning_assertion") == "Error"

    # names/owners/tags come from user code and are rendered with innerHTML - they must go through escHtml
    assert "if (typeof val === 'string') val = escHtml(val);" in html
    assert html.count("<span class=\"tag-chip\">${escHtml(tag)}</span>") == 2
    assert "<span class=\"tag-chip\">${tag}</span>" not in html
