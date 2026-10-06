# -*- coding: utf-8 -*-
import io
import math
import os

from test_junkie.constants import TestCategory


_STATUS_COLORS = {
    TestCategory.SUCCESS: "#12d479",
    TestCategory.FAIL:    "#fcd75f",
    TestCategory.ERROR:   "#ff7651",
    TestCategory.SKIP:    "#34bff5",
    TestCategory.IGNORE:  "#cce4eb",
    TestCategory.CANCEL:  "#f19def",
}

_STATUS_LABELS = {
    TestCategory.SUCCESS: "Success",
    TestCategory.FAIL:    "Fail",
    TestCategory.ERROR:   "Error",
    TestCategory.SKIP:    "Skip",
    TestCategory.IGNORE:  "Ignore",
    TestCategory.CANCEL:  "Cancel",
}

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_FONTS = '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">\n'


def _asset(name):
    """
    The report's CSS and JS ship as package data (reporter/assets) - as Python strings they were installed twice
    (source + compiled .pyc), ~150KB of a ~650KB install
    """
    with io.open(os.path.join(_ASSETS, name), encoding="utf-8") as doc:
        return doc.read()

_BRAND_SVG = """\
<svg class="brand-icon" viewBox="0 0 28 28" fill="none">
  <circle cx="14" cy="14" r="11" stroke="#f37814" stroke-width="1.4" stroke-dasharray="5 3" opacity=".6"/>
  <path d="M 25,14 A 11,11 0 0,0 14,3" stroke="#f37814" stroke-width="3" stroke-linecap="round"/>
  <circle cx="14" cy="14" r="6" stroke="#f37814" stroke-width="2"/>
  <line x1="3" y1="14" x2="8" y2="14" stroke="#f37814" stroke-width="1.6"/>
  <line x1="20" y1="14" x2="25" y2="14" stroke="#f37814" stroke-width="1.6"/>
  <line x1="14" y1="3" x2="14" y2="8" stroke="#f37814" stroke-width="1.6"/>
  <line x1="14" y1="20" x2="14" y2="25" stroke="#f37814" stroke-width="1.6"/>
  <polygon points="14,10 17,14 14,18 11,14" fill="#f37814"/>
  <circle cx="14" cy="14" r="1.5" fill="white" opacity=".9"/>
</svg>"""


class ReportTemplate:

    @staticmethod
    def render(data):
        ctx = ReportTemplate._build_context(data)
        return (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '<title>Test Junkie — Run Report</title>\n'
            + _FONTS + '<style>\n' + _asset("report.css") + '\n</style>\n</head>\n<body>\n'
            + ReportTemplate._header(ctx)
            + '<div class="container">\n'
            + ReportTemplate._stats(ctx)
            + ReportTemplate._charts_row(ctx)
            + ReportTemplate._breakdown(ctx)
            + ReportTemplate._results_section()
            + '</div>\n'
            + ReportTemplate._detail_panel()
            + ReportTemplate._threading_dialog()
            + ReportTemplate._support_fab()
            + ReportTemplate._support_modal()
            + ReportTemplate._scripts(ctx)
            + '</body>\n</html>\n'
        )

    # ── Context builder ───────────────────────────────────────────────────────

    @staticmethod
    def _build_context(data):
        totals = data["totals"]
        issues = data["issues"]

        if issues > 0:
            issue_badge = (
                f'<div class="run-status" style="background:color-mix(in srgb,var(--s-fail) 12%,'
                f'var(--surface-raised));border:1px solid color-mix(in srgb,var(--s-fail) 30%,'
                f'var(--border));color:var(--s-fail)">'
                f'<div class="run-status-dot" style="background:var(--s-fail)"></div>'
                f'{issues} issue{"s" if issues != 1 else ""}</div>'
            )
        else:
            issue_badge = (
                '<div class="run-status" style="background:color-mix(in srgb,var(--s-success) 12%,'
                'var(--surface-raised));border:1px solid color-mix(in srgb,var(--s-success) 30%,'
                'var(--border));color:var(--s-success)">'
                '<div class="run-status-dot" style="background:var(--s-success)"></div>stable</div>'
            )

        n_success = totals.get(TestCategory.SUCCESS, 0)
        n_total = totals.get("total", 0)
        suite_count = data.get("suite_count", 0)

        cpu_avg = data.get("cpu_avg", "—")
        cpu_peak = data.get("cpu_peak", "—")
        mem_avg = data.get("mem_avg", "—")
        mem_peak = data.get("mem_peak", "—")
        resources_enabled = data.get("resources_enabled", False)

        cpu_sub = f"peak {cpu_peak}" if cpu_peak != "—" else "not tracked"
        mem_sub = f"peak {mem_peak}" if mem_peak != "—" else "not tracked"

        runtime_str = data.get("runtime", "—")
        if resources_enabled:
            res_legend_style = ""
            res_enabled_style = ""
            res_disabled_style = "display:none"
            res_toggle_text = "Disable"
        else:
            res_legend_style = "display:none"
            res_enabled_style = "display:none"
            res_disabled_style = ""
            res_toggle_text = "Enable"

        return {
            "run_date": data.get("run_date", ""),
            "run_time": data.get("run_time", ""),
            "runtime": runtime_str,
            "issue_badge": issue_badge,
            "stat_total": str(n_total),
            "stat_suite_count": f"across {suite_count} suite{'s' if suite_count != 1 else ''}",
            "stat_passing_rate": totals.get("passing_rate", "0.0%"),
            "stat_passing_sub": f"{n_success} of {n_total} passed",
            "stat_runtime": runtime_str,
            "stat_avg_runtime": data.get("avg_runtime", "—"),
            "stat_cpu_avg": cpu_avg,
            "stat_cpu_sub": cpu_sub,
            "stat_mem_avg": mem_avg,
            "stat_mem_sub": mem_sub,
            "res_legend_style": res_legend_style,
            "res_enabled_style": res_enabled_style,
            "res_disabled_style": res_disabled_style,
            "res_toggle_text": res_toggle_text,
            "resource_svg": data.get("resource_svg", ""),
            "insights_html": ReportTemplate._build_insights(data.get("insights", [])),
            "donut_html": ReportTemplate._build_donut(totals),
            "totals": totals,
            "tests_json": data.get("tests_json", "[]"),
            "details_json": data.get("details_json", "{}"),
            "bar_data_json": data.get("bar_data_json", "{}"),
            "threading_data": data.get("threading_data"),
        }

    # ── Donut SVG ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_donut(totals):
        circ = 2 * math.pi * 72
        status_order = [
            (TestCategory.SUCCESS, "#12d479", "Success"),
            (TestCategory.FAIL,    "#fcd75f", "Fail"),
            (TestCategory.ERROR,   "#ff7651", "Error"),
            (TestCategory.SKIP,    "#34bff5", "Skip"),
            (TestCategory.IGNORE,  "#cce4eb", "Ignore"),
            (TestCategory.CANCEL,  "#f19def", "Cancel"),
        ]
        total = totals.get("total", 0)
        avg_dur = totals.get("avg_dur", {})

        if total == 0:
            return '<div style="padding:20px;text-align:center;color:var(--ink-faint)">No test data.</div>'

        circles = ['<circle cx="90" cy="90" r="72" fill="none" stroke="#1c2129" stroke-width="22"/>']
        table_rows = []
        offset = 0.0

        col_header = (
            '<div style="display:grid;grid-template-columns:1fr 60px 60px 80px;gap:0;'
            'border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:6px;">'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace">Status</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">Count</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">%</span>'
            '<span style="font-size:10px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;'
            'color:var(--ink-faint);font-family:\'IBM Plex Mono\',monospace;text-align:right">Avg dur</span>'
            '</div>'
        )

        active_statuses = [(s, c, l) for s, c, l in status_order if totals.get(s, 0) > 0]
        last_idx = len(active_statuses) - 1

        for i, (status, color, label) in enumerate(active_statuses):
            count = totals.get(status, 0)
            arc = count / total * circ
            circles.append(
                f'<circle cx="90" cy="90" r="72" fill="none" stroke="{color}" stroke-width="22" '
                f'stroke-dasharray="{arc:.1f} {circ:.1f}" stroke-dashoffset="-{offset:.1f}" '
                f'transform="rotate(-90 90 90)" stroke-linecap="butt"/>'
            )
            pct = count / total * 100
            dur = avg_dur.get(status, "—")
            border = "" if i == last_idx else "border-bottom:1px solid var(--border);"
            table_rows.append(
                f'<div style="display:grid;grid-template-columns:1fr 60px 60px 80px;gap:0;'
                f'align-items:center;padding:5px 0;{border}">'
                f'<span style="display:flex;align-items:center;gap:7px;font-size:12px;color:var(--ink-muted)">'
                f'<span style="width:8px;height:8px;border-radius:2px;background:{color};'
                f'display:inline-block;flex:none"></span>{label}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;font-weight:600;'
                f'color:var(--ink);text-align:right">{count}</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;'
                f'color:var(--ink-muted);text-align:right">{pct:.1f}%</span>'
                f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:12px;'
                f'color:var(--ink-muted);text-align:right">{dur}</span>'
                f'</div>'
            )
            offset += arc

        circles_svg = "\n".join(circles)
        table_html = "\n".join(table_rows)
        return (
            '<div style="display:flex;align-items:center;gap:48px;justify-content:center;padding:8px 0;">'
            '<div style="flex:none">'
            f'<svg class="donut-svg" width="160" height="160" viewBox="0 0 180 180">'
            f'{circles_svg}'
            f'<text x="90" y="84" class="donut-center-label" fill="#e6edf3" font-size="26" font-weight="700" '
            f'font-family="\'IBM Plex Mono\',monospace">{total}</text>'
            f'<text x="90" y="102" class="donut-center-label" fill="#6e7681" font-size="11" '
            f'font-family="\'IBM Plex Mono\',monospace">tests</text>'
            f'</svg></div>'
            '<div style="display:flex;flex-direction:column;gap:0;min-width:260px;">'
            + col_header + table_html +
            '</div></div>'
        )

    # ── Insights ──────────────────────────────────────────────────────────────

    @staticmethod
    def _build_insights(insights):
        import html as _html
        if not insights:
            return (
                '<div class="insight-item ok">'
                '<div class="insight-icon">✓</div>'
                '<div>All tests completed. No significant issues detected.</div>'
                '</div>'
            )
        parts = []
        for item in insights:  # dicts from the Analyzer: text, traceback, test_ids
            text = item.get("text", "")
            traceback_str = item.get("traceback")
            test_ids = item.get("test_ids", [])
            tl = text.lower()
            if "stable" in tl or "no time" in tl:
                cls, icon = "ok", "✓"
            elif "retr" in tl or "traceback" in tl or "unique" in tl or "similar" in tl:
                cls, icon = "warn", "⚠"
            else:
                cls, icon = "info", "▸"
            safe = _html.escape(text)
            dialog = item.get("dialog") if isinstance(item, dict) else None
            chip_html = ""
            if dialog and dialog.get("type") == "threading":
                chip_html = (
                    '<button class="thread-chip" onclick="openThreadingDialog()">'
                    '&#x26A1; analyze threading'
                    '</button>'
                )
            elif traceback_str and test_ids:
                ids_json = ",".join(str(i) for i in test_ids)
                tb_escaped = _html.escape(traceback_str, quote=True)
                chip_html = (
                    f'<button class="traceback-chip" '
                    f'title="{tb_escaped}" '
                    f'onclick="applyTracebackFilter([{ids_json}])">'
                    f'&#x1F4CB; filter {len(test_ids)} tests'
                    f'</button>'
                )
            parts.append(
                f'<div class="insight-item {cls}">'
                f'<div class="insight-icon">{icon}</div>'
                f'<div>{safe}{chip_html}</div></div>'
            )
        return "\n".join(parts)

    # ── Header ────────────────────────────────────────────────────────────────

    @staticmethod
    def _header(ctx):
        return (
            '<header>\n<div class="container header-inner">\n'
            f'<a class="brand" href="https://www.test-junkie.com" target="_blank" rel="noopener" style="text-decoration:none">'
            f'{_BRAND_SVG}'
            f'<span class="brand-name">TEST<span>JUNKIE</span></span>'
            f'</a>\n'
            f'<div class="header-meta">'
            f'<span>{ctx["run_date"]} &middot; {ctx["run_time"]}</span>'
            f'<span>{ctx["runtime"]} total</span>'
            f'{ctx["issue_badge"]}'
            f'<button class="theme-toggle" id="theme-toggle" title="Toggle light / dark mode">'
            f'<svg id="theme-icon-dark" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            f'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/>'
            f'<line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>'
            f'<line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>'
            f'<line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/>'
            f'<line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>'
            f'<line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
            f'<svg id="theme-icon-light" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="display:none">'
            f'<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
            f'</button>'
            f'</div>\n'
            f'</div>\n</header>\n'
        )

    # ── Stat cards ────────────────────────────────────────────────────────────

    @staticmethod
    def _stats(ctx):
        def card(label, value, sub, brand=False):
            cls = 'stat-value brand' if brand else 'stat-value'
            return (
                f'<div class="stat-card">'
                f'<div class="stat-label">{label}</div>'
                f'<div class="{cls}">{value}</div>'
                f'<div class="stat-sub">{sub}</div>'
                f'</div>'
            )
        return (
            '<div class="stats-row">\n'
            + card("Tests Executed", ctx["stat_total"], ctx["stat_suite_count"])
            + card("Passing Rate", ctx["stat_passing_rate"], ctx["stat_passing_sub"], brand=True)
            + card("Total Runtime", ctx["stat_runtime"], "wall-clock time")
            + card("Avg Test Runtime", ctx["stat_avg_runtime"], "@test only")
            + card("Avg CPU", ctx["stat_cpu_avg"], ctx["stat_cpu_sub"])
            + card("Avg Memory", ctx["stat_mem_avg"], ctx["stat_mem_sub"])
            + '\n</div>\n'
        )

    # ── Charts row ────────────────────────────────────────────────────────────

    @staticmethod
    def _charts_row(ctx):
        resource_body = (
            f'<div id="res-enabled" class="resource-chart-wrap" style="{ctx["res_enabled_style"]}">'
            + ctx["resource_svg"]
            + '</div>\n'
            '<div id="res-disabled" class="resource-disabled"'
            f' style="{ctx["res_disabled_style"]}">'
            '<div class="resource-disabled-icon">&#x1F4CA;</div>'
            '<div class="resource-disabled-msg">'
            'Resource monitoring was not enabled for this run.<br>'
            'To track CPU and memory usage, pass<br>'
            '<code>monitor_resources=True</code> to your runner.'
            '</div></div>\n'
        )
        return (
            '<div class="charts-row">\n'
            '<div class="chart-card" style="display:flex;flex-direction:column;">\n'
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
            '<div class="card-title" style="margin-bottom:0">Resource Monitoring</div>'
            '<div style="display:flex;align-items:center;gap:14px;">'
            f'<div id="res-legend" style="display:flex;align-items:center;gap:14px;{ctx["res_legend_style"]}">'
            '<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:\'IBM Plex Mono\',monospace;color:var(--ink-muted)">'
            '<span style="display:inline-block;width:18px;height:2px;background:var(--brand);border-radius:1px;vertical-align:middle"></span>CPU</span>'
            '<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:\'IBM Plex Mono\',monospace;color:var(--ink-muted)">'
            '<span style="display:inline-block;width:18px;height:2px;background:#34bff5;border-radius:1px;vertical-align:middle"></span>Memory</span>'
            '</div>'
            f'<button class="resource-toggle-btn" id="res-toggle-btn" onclick="toggleResources()">{ctx["res_toggle_text"]}</button>'
            '</div></div>\n'
            + resource_body
            + '</div>\n'
            '<div class="chart-card">\n'
            '<div class="card-title">Insights</div>'
            '<div class="insights-list">'
            + ctx["insights_html"]
            + '</div></div>\n'
            '</div>\n'
        )

    # ── Breakdown tabs ────────────────────────────────────────────────────────

    @staticmethod
    def _breakdown(ctx):
        return (
            '<div class="breakdown-section">\n'
            '<div class="breakdown-card">\n'
            '<div class="tab-bar">'
            '<button class="tab-btn" data-tab="results">Results</button>'
            '<button class="tab-btn active" data-tab="features">Features</button>'
            '<button class="tab-btn" data-tab="components">Components</button>'
            '<button class="tab-btn" data-tab="owners">Owners</button>'
            '<button class="tab-btn" data-tab="suites">Suites</button>'
            '<button class="tab-btn" data-tab="tags">Tags</button>'
            '</div>\n'
            f'<div class="tab-content" id="tab-results">{ctx["donut_html"]}</div>\n'
            '<div class="tab-content active" id="tab-features"><div id="chart-features"></div></div>\n'
            '<div class="tab-content" id="tab-components"><div id="chart-components"></div></div>\n'
            '<div class="tab-content" id="tab-owners"><div id="chart-owners"></div></div>\n'
            '<div class="tab-content" id="tab-suites"><div id="chart-suites"></div></div>\n'
            '<div class="tab-content" id="tab-tags"><div id="chart-tags"></div></div>\n'
            '</div>\n</div>\n'
        )

    # ── Results table section ─────────────────────────────────────────────────

    @staticmethod
    def _results_section():
        return (
            '<div class="results-section">\n'
            '<div class="results-card">\n'
            '<div class="results-header">'
            '<div class="results-title">Test Results'
            '<span class="results-count" id="visible-count">— tests</span>'
            '</div>'
            '<div class="search-global">'
            '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'
            '<input type="text" id="global-search" placeholder="Search all columns…">'
            '</div></div>\n'
            '<div class="filter-bar" id="filter-bar">'
            '<span class="filter-label">Filters</span>'
            '<button class="filter-clear-all" id="clear-all-btn">Clear all \xd7</button>'
            '<div class="tb-filter-strip" id="tb-filter-strip">'
            'Traceback group active'
            '<button class="tb-filter-clear" onclick="clearTracebackFilter()" title="Clear traceback filter">\xd7</button>'
            '</div>'
            '</div>\n'
            '<div class="table-wrap">'
            '<table id="results-table">'
            '<thead><tr id="table-head"></tr></thead>'
            '<tbody id="table-body"></tbody>'
            '</table></div>\n'
            '</div>\n</div>\n'
        )

    # ── Threading analysis dialog ─────────────────────────────────────────────

    @staticmethod
    def _threading_dialog():
        return (
            '<div id="thread-backdrop" onclick="closeThreadingDialog()"></div>\n'
            '<div id="thread-dialog" role="dialog" aria-modal="true" aria-labelledby="td-title">\n'
            '<div class="td-header">'
            '<div class="td-title" id="td-title">&#x26A1; Multi-threading Analysis</div>'
            '<button class="td-close" onclick="closeThreadingDialog()" aria-label="Close">&#x2715;</button>'
            '</div>\n'
            '<div class="td-summary" id="td-summary"></div>\n'
            '<div class="td-section-label">Enable in your runner</div>\n'
            '<div class="td-code-wrap" id="td-code"></div>\n'
            '<div class="td-section-label" style="margin-top:20px">Slowest tests &#x2014; bottleneck candidates</div>\n'
            '<table class="td-table"><thead><tr>'
            '<th>Test</th><th>Suite</th><th style="text-align:right">Duration</th>'
            '</tr></thead><tbody id="td-tbody"></tbody></table>\n'
            '<div class="td-note" id="td-note"></div>\n'
            '</div>\n'
        )

    # ── Detail panel ──────────────────────────────────────────────────────────

    @staticmethod
    def _detail_panel():
        return (
            '<div id="overlay"></div>\n'
            '<div id="detail-panel">\n'
            '<div class="panel-header">'
            '<div style="flex:1;min-width:0">'
            '<div class="panel-test-name" id="panel-test-name">—</div>'
            '<div class="panel-suite-path" id="panel-suite-path">—</div>'
            '<div class="panel-tags" id="panel-tags"></div>'
            '</div>'
            '<button class="panel-close" id="panel-close">✕</button>'
            '</div>\n'
            '<div class="panel-body" id="panel-body"></div>\n'
            '</div>\n'
        )

    # ── Support FAB ───────────────────────────────────────────────────────────

    @staticmethod
    def _support_fab():
        return (
            '<button id="support-fab" title="Support this project" aria-label="Support this project">'
            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 '
            '7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>'
            '</svg></button>\n'
        )

    # ── Support modal ─────────────────────────────────────────────────────────

    @staticmethod
    def _support_modal():
        logo = _BRAND_SVG.replace('class="brand-icon"', 'width="32" height="32"')
        return (
            '<div id="support-backdrop"></div>\n'
            '<div id="support-modal" role="dialog" aria-modal="true" aria-labelledby="support-title">\n'
            '<button class="support-close" id="support-close" aria-label="Close">✕</button>\n'
            f'<div class="support-logo">{logo}</div>\n'
            '<h2 class="support-title" id="support-title">Support Test Junkie</h2>\n'
            '<p class="support-message">Test Junkie is a solo open-source project. If it has saved you '
            'time writing runners, fighting flaky tests, or debugging parallel execution — '
            'a star or a coffee goes a long way and helps keep it maintained.</p>\n'
            '<div class="support-options">\n'
            '<a class="support-option" href="https://github.com/ArturSpirin/test_junkie" target="_blank" rel="noopener">'
            '<div class="support-option-icon">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 '
            '0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 '
            '1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 '
            '0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 '
            '1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 '
            '1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 '
            '0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Star on GitHub</div>'
            '<div class="support-option-sub">Show you use it \xb7 costs nothing</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '<a class="support-option" href="https://www.patreon.com/join/arturspirin" target="_blank" rel="noopener">'
            '<div class="support-option-icon" style="color:#ff424d">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M22.957 7.21c-.004-3.064-2.391-5.576-5.191-6.482-3.478-1.125-8.064-.962-11.384.604C2.357 3.231 '
            '1.093 7.391 1.046 11.54c-.039 3.411.302 12.396 5.369 12.46 3.765.047 4.326-4.804 6.068-7.141 '
            '1.24-1.662 2.836-2.132 4.801-2.618 3.376-.836 5.678-3.501 5.673-7.031Z"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Support on Patreon</div>'
            '<div class="support-option-sub">Monthly support \xb7 keeps the lights on</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '<a class="support-option" href="https://www.paypal.com/cgi-bin/webscr?cmd=_donations&amp;business=FJPYWX5B776YS&amp;currency_code=USD&amp;source=url" target="_blank" rel="noopener">'
            '<div class="support-option-icon" style="color:#009cde">'
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">'
            '<path d="M7.016 19.198h-4.2a.562.562 0 0 1-.555-.65L5.093.584A.692.692 0 0 1 5.776 0h7.222c3.417 '
            '0 5.904 2.488 5.846 5.5-.006.25-.027.5-.066.747A6.794 6.794 0 0 1 12.071 12H8.743a.69.69 0 0 '
            '0-.682.583l-.325 2.056-.013.083-.692 4.39-.015.087zM19.79 6.142c-.01.087-.01.175-.023.261a7.76 '
            '7.76 0 0 1-7.695 6.598H9.007l-.283 1.795-.013.083-.692 4.39-.134.843-.014.088H6.86l-.497 3.15a.562.562 '
            '0 0 0 .555.65h3.612c.34 0 .63-.249.683-.585l.952-6.031a.692.692 0 0 1 .683-.584h2.126a6.793 6.793 '
            '0 0 0 6.707-5.752c.306-1.95-.466-3.744-1.89-4.906z"/>'
            '</svg></div>'
            '<div class="support-option-text">'
            '<div class="support-option-label">Donate via PayPal</div>'
            '<div class="support-option-sub">One-time \xb7 any amount appreciated</div>'
            '</div>'
            '<svg class="support-option-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<polyline points="9 18 15 12 9 6"/></svg></a>\n'
            '</div>\n</div>\n'
        )

    # ── Scripts ───────────────────────────────────────────────────────────────

    @staticmethod
    def _scripts(ctx):
        import json as _json
        tests_json = ctx["tests_json"].replace("</", "<\\/")
        details_json = ctx["details_json"].replace("</", "<\\/")
        bar_data_json = ctx["bar_data_json"].replace("</", "<\\/")
        threading_json = _json.dumps(ctx.get("threading_data")).replace("</", "<\\/")

        resources_enabled = "true" if ctx.get("res_enabled_style", "display:none") == "" else "false"
        return ("<script>\nconst TESTS = " + tests_json + ";\nconst DETAILS = " + details_json
                + ";\nconst BAR_DATA = " + bar_data_json + ";\nconst THREADING_DATA = " + threading_json
                + ";\nconst RESOURCES_ENABLED = " + resources_enabled + ";\n" + _asset("report.js") + "</script>\n")
