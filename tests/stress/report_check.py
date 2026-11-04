"""
Correctness check for the reports one stress size kept (report_stress.py --out DIR): report.xml, report.html and
expected.json, what the generated run was. Generated data only.

    python3.13 -m tests.stress.report_check OUT/<size> [--browser] [--screenshot PNG]

XML: parses with xml.etree, validates against the Jenkins xUnit plugin's JUnit schema (xsd/junit-10.xsd, see the
README), counts read from the <testsuite> attributes and from the elements. HTML: counts read from the page's own data
(TESTS, the Tests Executed card), and with --browser from the page as headless Chromium shows it, with the time to load
it and to open, expand and scroll the failure list. Timings are reported, never judged here.
"""
import argparse
import collections
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ElementTree

XSD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xsd", "junit-10.xsd")
COUNTS = ("tests", "passed", "failures", "errors", "skipped", "reruns")
RERUN_TAGS = ("rerunFailure", "rerunError", "flakyFailure", "flakyError")
HTML_STATUS = {"success": "passed", "fail": "failures", "error": "errors", "skip": "skipped"}


def expected(folder):
    with open(os.path.join(folder, "expected.json"), encoding="utf-8") as source:
        return json.load(source)


# ── XML ─────────────────────────────────────────────────────────────────────────────────────────────────────────────

def xml_counts(path):
    """
    {"seconds": parse time, "attributes": counts summed from the <testsuite> attributes (None when the attribute is
    on no suite), "elements": counts from the <testcase> children, by JUnit meaning}
    """
    begin = time.perf_counter()
    root = ElementTree.parse(path).getroot()
    seconds = time.perf_counter() - begin
    suites = list(root.iter("testsuite"))

    def total(name):
        values = [int(suite.get(name)) for suite in suites if suite.get(name) is not None]
        return sum(values) if values else None
    attributes = {name: total(name) for name in ("tests", "passed", "failures", "errors", "skipped")}
    if attributes["passed"] is None and attributes["tests"] is not None:  # junit-10 has no passed= (TASK-1315)
        attributes["passed"] = attributes["tests"] - sum(attributes[name] or 0
                                                         for name in ("failures", "errors", "skipped"))
    elements = collections.Counter(tests=0, passed=0, failures=0, errors=0, skipped=0, reruns=0)
    for case in root.iter("testcase"):
        elements["tests"] += 1
        tags = [child.tag for child in case]
        if "skipped" in tags:
            elements["skipped"] += 1
        elif "error" in tags:
            elements["errors"] += 1
        elif "failure" in tags:
            elements["failures"] += 1
        else:
            elements["passed"] += 1
        elements["reruns"] += sum(1 for tag in tags if tag in RERUN_TAGS)
    return {"seconds": seconds, "root": root.tag, "attributes": attributes, "elements": dict(elements)}


def _kind(error):
    """An error's kind: its reason with the numbers and test names taken out, so the same problem counts once"""
    reason = getattr(error, "reason", None) or str(error).splitlines()[0]
    reason = re.sub(r"'test_\d+[^']*'|'StressSuite\d+'", "'<name>'", reason)
    return re.sub(r"\d+", "N", reason)


def validate_xml(path, schema_path=XSD, examples=3):
    """
    Validates the file against the schema (xmlschema, lazy: a large file streams). An undeclared root is one error and
    validation still goes on into its children, so every kind of problem is counted. Returns {"valid": bool,
    "seconds", "errors": {kind: count}, "examples": {kind: [first messages]}}
    """
    import xmlschema
    begin = time.perf_counter()
    schema = xmlschema.XMLSchema10(schema_path)
    found = collections.Counter()
    shown = collections.defaultdict(list)
    for error in schema.iter_errors(xmlschema.XMLResource(path, lazy=True)):
        kind = _kind(error)
        found[kind] += 1
        if len(shown[kind]) < examples:
            shown[kind].append("{} at {}".format(getattr(error, "reason", None) or error, getattr(error, "path", None)))
    return {"valid": not found, "seconds": time.perf_counter() - begin, "errors": dict(found),
            "examples": dict(shown)}


# ── HTML ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _page_constant(text, name):
    start = text.index("const {} = ".format(name)) + len("const {} = ".format(name))
    return json.JSONDecoder().raw_decode(text, start)[0]


def html_counts(path):
    """Counts from the page's own data without a browser: the TESTS rows by status, their retries, and the cards"""
    with open(path, encoding="utf-8") as source:
        text = source.read()
    tests = _page_constant(text, "TESTS")
    counts = collections.Counter(tests=len(tests), passed=0, failures=0, errors=0, skipped=0, reruns=0)
    other = collections.Counter()
    for row in tests:
        if row["status"] in HTML_STATUS:
            counts[HTML_STATUS[row["status"]]] += 1
        else:
            other[row["status"]] += 1
        counts["reruns"] += row["retries"]
    card = re.search(r'stat-label">Tests Executed</div><div class="stat-value">(\d+)<', text)
    passing = re.search(r'stat-sub">(\d+) of (\d+) passed<', text)
    return {"bytes": len(text.encode("utf-8")), "counts": dict(counts), "other_statuses": dict(other),
            "card_tests": int(card.group(1)) if card else None,
            "card_passed": int(passing.group(1)) if passing else None,
            "card_of": int(passing.group(2)) if passing else None}


def browser_check(path, reruns, timeout=600.0, screenshot=None, offline=False):
    """
    Opens the report in headless Chromium and uses it as a person would: waits for the table, filters it to the
    failures and errors, wheels down to the last of them, opens the first one's detail panel, expands its first
    attempt and wheels the panel to the bottom. offline=True aborts every request that isn't a file (the fonts), so
    the time doesn't depend on the network. Returns {"seconds": {step: s}, "counts", "status_menu", "problems": [...]};
    a step that breaks goes in problems (and the steps after it that need it are skipped)
    """
    from playwright.sync_api import sync_playwright
    result = {"seconds": {}, "counts": None, "status_menu": None, "problems": []}
    seconds = result["seconds"]
    ms = timeout * 1000

    def timed(step, func):
        begin = time.perf_counter()
        try:
            return func()
        finally:
            seconds[step] = time.perf_counter() - begin

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.set_default_timeout(ms)
            if offline:
                page.route(re.compile(r"^(?!file:)"), lambda route: route.abort())
            url = "file:///" + os.path.abspath(path).replace(os.sep, "/").lstrip("/")
            # the page links a Google Fonts stylesheet, which holds "load" for as long as the network takes: the
            # report's own cost is the time to DOMContentLoaded and then to the table
            timed("dom_loaded", lambda: page.goto(url, wait_until="domcontentloaded", timeout=ms))
            timed("load_after_dom", lambda: page.wait_for_load_state("load", timeout=ms))
            total = page.evaluate("TESTS.length")
            timed("table", lambda: page.wait_for_function(
                "n => document.getElementById('visible-count').textContent === n + ' test' + (n !== 1 ? 's' : '')"
                " && document.querySelectorAll('#table-body tr').length === n", arg=total, timeout=ms))
            result["counts"] = page.evaluate("""() => {
                const by = {success: 'passed', fail: 'failures', error: 'errors', skip: 'skipped'};
                const c = {tests: TESTS.length, passed: 0, failures: 0, errors: 0, skipped: 0, reruns: 0};
                TESTS.forEach(t => { if (by[t.status]) c[by[t.status]] += 1; c.reruns += t.retries; });
                c.rows = document.querySelectorAll('#table-body tr').length;
                return c; }""")
            result["status_menu"] = page.evaluate("""() => Object.fromEntries(
                [...document.querySelectorAll('#fmi-status .filter-menu-item')].map(item =>
                    [item.querySelector('input').value, parseInt(item.querySelector('.item-count').textContent)]))""")
            bad = [status for status in ("fail", "error") if status in result["status_menu"]]
            want = sum(result["status_menu"][status] for status in bad)
            if not want:
                result["problems"].append("no fail or error in the status filter: {}".format(result["status_menu"]))
                return result

            def filter_failures():
                page.click("#fb-status")
                for status in bad:
                    page.check("#chk-status-{}".format(status))
                page.wait_for_function(
                    "n => document.querySelectorAll('#table-body tr').length === n", arg=want, timeout=ms)
                page.mouse.click(5, 5)  # closes the menu, as a click outside it does
            timed("filter", filter_failures)
            statuses = page.eval_on_selector_all("#table-body tr .badge", "els => [...new Set(els.map(e => e.textContent))]")
            if sorted(statuses) != sorted(bad):
                result["problems"].append("the failure list shows statuses {}".format(statuses))

            def wheel_until(position, check):
                """Mouse-wheel at position until check() (a JS function returning {done, at}) is done; a wheel turn
                that doesn't move `at` within 2 s ends it: the page or panel can't scroll further"""
                from playwright.sync_api import TimeoutError as PlaywrightTimeout
                page.mouse.move(*position)
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    state = page.evaluate(check)
                    if state["done"]:
                        return True
                    page.mouse.wheel(0, 2000)
                    try:
                        page.wait_for_function("([check, at]) => eval(check)().at !== at", arg=[check, state["at"]],
                                               timeout=2000)
                    except PlaywrightTimeout:
                        return page.evaluate(check)["done"]
                return False

            def scroll_to_last():
                return wheel_until((400, 450), """() => { const rows = document.querySelectorAll('#table-body tr');
                    const box = rows[rows.length - 1].getBoundingClientRect();
                    return {done: box.top >= 0 && box.bottom <= window.innerHeight && window.scrollY > 0,
                            at: window.scrollY}; }""")
            if not timed("scroll_list", scroll_to_last):
                result["problems"].append("the last failure row is not in view after scrolling to it")
            page.evaluate("window.scrollTo(0, 0)")

            def open_first():
                page.locator("#table-body tr").first.click()
                page.wait_for_selector("#detail-panel.open", state="attached", timeout=ms)
                page.wait_for_function("() => document.getElementById('detail-panel').getBoundingClientRect().left"
                                       " < window.innerWidth - 100", timeout=ms)  # slid in
            timed("open_panel", open_first)
            attempts = page.locator("#panel-body .attempt").count()
            if attempts != reruns + 1:
                result["problems"].append("the panel lists {} attempts, expected {}".format(attempts, reruns + 1))

            def expand_attempt():
                page.locator("#panel-body .variant-header").first.click()
                page.locator("#panel-body .attempt-header").first.click()
                body = page.locator("#panel-body .attempt.expanded .attempt-body").first
                body.wait_for(state="visible", timeout=ms)
                return body.inner_text()
            text = timed("expand_attempt", expand_attempt)
            if "synthetic failure" not in text:
                result["problems"].append("the expanded attempt shows no traceback: {!r}".format(text[:200]))
            if screenshot:
                page.screenshot(path=screenshot)

            def scroll_panel():
                box = page.locator("#panel-body").bounding_box()
                return wheel_until((box["x"] + box["width"] / 2, box["y"] + box["height"] / 2), """() => {
                    const el = document.getElementById('panel-body');
                    return {done: el.scrollHeight > el.clientHeight && el.scrollTop >= el.scrollHeight - el.clientHeight - 1,
                            at: el.scrollTop}; }""")
            if not timed("scroll_panel", scroll_panel):
                result["problems"].append("the panel did not scroll to its end: {}".format(page.evaluate(
                    "() => { const el = document.getElementById('panel-body');"
                    " return {top: el.scrollTop, height: el.scrollHeight, view: el.clientHeight}; }")))
        finally:
            browser.close()
    return result


# ── One size ────────────────────────────────────────────────────────────────────────────────────────────────────────

def check_size(folder, browser=False, screenshot=None, timeout=600.0, offline=False):
    want = expected(folder)
    result = {"expected": {name: want[name] for name in COUNTS}, "size": want["size"],
              "xml": xml_counts(os.path.join(folder, "report.xml")),
              "xsd": validate_xml(os.path.join(folder, "report.xml")),
              "html": html_counts(os.path.join(folder, "report.html"))}
    if browser:
        result["browser"] = browser_check(os.path.join(folder, "report.html"), want["size"]["reruns"], timeout,
                                          screenshot, offline)
    return result


def counts_table(result):
    columns = [("generated", result["expected"]), ("XML attributes", result["xml"]["attributes"]),
               ("XML elements", result["xml"]["elements"]), ("HTML data", result["html"]["counts"])]
    if result.get("browser") and result["browser"]["counts"]:
        columns.append(("HTML in Chromium", result["browser"]["counts"]))
    lines = ["| count | " + " | ".join(name for name, _ in columns) + " |",
             "|---|" + "---|" * len(columns)]
    for count in COUNTS:
        cells = []
        for _, values in columns:
            value = values.get(count)
            cell = "-" if value is None else str(value)
            if value != result["expected"][count]:
                cell = "**{}**".format(cell)  # differs from the generated run
            cells.append(cell)
        lines.append("| {} | {} |".format(count, " | ".join(cells)))
    return "\n".join(lines)


def format_result(folder, result):
    xsd, html = result["xsd"], result["html"]
    lines = ["## {}".format(os.path.basename(os.path.normpath(folder))),
             "XML: parsed in {:.2f} s, root <{}>; junit-10.xsd: {} ({:.2f} s)".format(
                 result["xml"]["seconds"], result["xml"]["root"], "valid" if xsd["valid"] else "INVALID",
                 xsd["seconds"])]
    for kind, count in sorted(xsd["errors"].items()):
        lines.append("  x{}: {}".format(count, kind))
        lines.extend("      e.g. {}".format(example[:300]) for example in xsd["examples"][kind][:1])
    lines.append("HTML: {:.1f} MB; Tests Executed card {}, {} of {} passed{}".format(
        html["bytes"] / 1048576.0, html["card_tests"], html["card_passed"], html["card_of"],
        "; other statuses {}".format(html["other_statuses"]) if html["other_statuses"] else ""))
    lines.append(counts_table(result))
    if result.get("browser"):
        run = result["browser"]
        lines.append("Chromium: " + ", ".join("{} {:.2f} s".format(step, s) for step, s in run["seconds"].items()))
        lines.append("  status filter counts {}; problems: {}".format(run["status_menu"], run["problems"] or "none"))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m tests.stress.report_check", description=__doc__.split("\n\n")[0])
    parser.add_argument("folders", nargs="+", help="size folders report_stress.py --out kept")
    parser.add_argument("--browser", action="store_true", help="also open the HTML report in headless Chromium")
    parser.add_argument("--screenshot", help="with --browser: a PNG of the open failure panel (last folder)")
    parser.add_argument("--timeout", type=float, default=600.0, help="seconds per browser action (default 600)")
    parser.add_argument("--offline", action="store_true", help="with --browser: block every non-file request (fonts)")
    parser.add_argument("--json", help="also write the full results to this file")
    args = parser.parse_args(argv)
    results = {}
    for folder in args.folders:
        result = check_size(folder, args.browser, args.screenshot, args.timeout, args.offline)
        results[folder] = result
        print(format_result(folder, result), flush=True)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as out:
            json.dump(results, out, indent=2, default=str)


if __name__ == "__main__":
    sys.exit(main())
