# -*- coding: utf-8 -*-
import io
import json
import math
import os
import re

from test_junkie.constants import TestCategory

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _asset(name):
    """
    The report's page, CSS and JS ship as package data (reporter/assets). As Python strings they were installed
    twice (source + compiled .pyc)
    """
    with io.open(os.path.join(_ASSETS, name), encoding="utf-8") as doc:
        return doc.read()


class ReportTemplate:

    @staticmethod
    def render(data):
        ctx = ReportTemplate._build_context(data)
        values = dict((key, value) for key, value in ctx.items() if isinstance(value, str))
        values.update({"css": _asset("report.css"), "js": _asset("report.js"),
                       "tests_json": ctx["tests_json"].replace("</", "<\\/"),
                       "details_json": ctx["details_json"].replace("</", "<\\/"),
                       "bar_data_json": ctx["bar_data_json"].replace("</", "<\\/"),
                       "threading_json": json.dumps(ctx.get("threading_data")).replace("</", "<\\/"),
                       "resources_enabled": "true" if ctx["res_enabled_style"] == "" else "false"})
        # one pass, so a value that happens to contain {{...}} is never substituted again
        return re.sub(r"\{\{(\w+)\}\}", lambda match: values[match.group(1)], _asset("report.html"))

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
