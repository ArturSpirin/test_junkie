# -*- coding: utf-8 -*-
import copy
import html as html_module
import json
import math
import os
import re
import time
import traceback
from datetime import datetime
from statistics import mean, median

from test_junkie.constants import TestCategory, DecoratorType
from test_junkie.debugger import LogJunkie
from test_junkie.metrics import Aggregator
from test_junkie.reporter.analyzer import Analyzer
from test_junkie.reporter.html_template import ReportTemplate


class Reporter:

    @staticmethod
    def round(value):
        return str(float("{0:.2f}".format(float(mean(value))))) if value else "0"

    @staticmethod
    def total_up(value):
        return str(float("{0:.2f}".format(float(sum(value))))) if value else "0"

    @staticmethod
    def escape(s, quote=True):
        return html_module.escape(s, quote=quote)

    def __init__(self, monitoring_file, aggregator, runtime, multi_threading_enabled):

        self.analyzer = Analyzer(monitoring_enabled=monitoring_file,
                                 multi_threading_enabled=multi_threading_enabled)
        self.monitoring_file = monitoring_file
        self.aggregator = aggregator
        self.runtime = runtime
        self.features = aggregator.get_report_by_features()
        self.tags = aggregator.get_report_by_tags()
        self.test_totals = aggregator.get_basic_report()["tests"]
        self.owners = aggregator.get_report_by_owner()
        self.suites = aggregator.get_report_by_suite()
        self.average_runtime = aggregator.get_average_test_runtime()

        self.__cpu_average = "—"
        self.__cpu_peak = "—"
        self.__mem_average = "—"
        self.__mem_peak = "—"
        self._thread_tasks = []

    # ── Public entry point ────────────────────────────────────────────────────

    def generate_html_report(self, write_file):

        resource_data = None
        resources_enabled = False
        if self.monitoring_file is not None:
            resource_data = self.__get_resources_data()
            resources_enabled = True

        table_data = self.__get_table_data()
        insights = self.__get_plain_insights()
        threading_data = next(
            (i["dialog"] for i in insights
             if isinstance(i, dict) and i.get("dialog", {}).get("type") == "threading"),
            None
        )

        totals = self.__build_totals(table_data["status_durations"])
        issues = (totals.get(TestCategory.FAIL, 0)
                  + totals.get(TestCategory.ERROR, 0)
                  + totals.get(TestCategory.CANCEL, 0))

        approx_start = datetime.fromtimestamp(time.time() - self.runtime)
        run_date = approx_start.strftime("%Y-%m-%d")
        run_time = approx_start.strftime("%H:%M:%S")

        avg_rt_sec = self.average_runtime if self.average_runtime else 0
        if avg_rt_sec >= 3600:
            avg_runtime_str = time.strftime("%Hh:%Mm:%Ss", time.gmtime(avg_rt_sec))
        elif avg_rt_sec >= 60:
            avg_runtime_str = time.strftime("%Mm:%Ss", time.gmtime(avg_rt_sec))
        else:
            avg_runtime_str = "{:.2f}s".format(avg_rt_sec)

        template_data = {
            "totals": totals,
            "issues": issues,
            "run_date": run_date,
            "run_time": run_time,
            "runtime": time.strftime("%Hh:%Mm:%Ss", time.gmtime(self.runtime)),
            "avg_runtime": avg_runtime_str,
            "cpu_avg": self.__cpu_average,
            "cpu_peak": self.__cpu_peak,
            "mem_avg": self.__mem_average,
            "mem_peak": self.__mem_peak,
            "resources_enabled": resources_enabled,
            "resource_svg": self.__build_resource_svg(resource_data),
            "insights": insights,
            "threading_data": threading_data,
            "tests_json": json.dumps(table_data["tests_data"]),
            "details_json": json.dumps(table_data["details_data"]),
            "bar_data_json": json.dumps(self.__get_bar_data()),
            "suite_count": len(self.aggregator.executed_suites),
        }

        html_content = ReportTemplate.render(template_data)
        os.makedirs(os.path.dirname(os.path.abspath(write_file)), exist_ok=True)  # e.g. html_report="reports/"
        with open(write_file, "w+", encoding="utf8") as output:
            output.write(html_content)

    # ── Resource monitoring ───────────────────────────────────────────────────

    def __get_resources_data(self):
        data = []
        cpu_samples = []
        mem_samples = []
        with open(self.monitoring_file, "r") as f:
            for line in f.readlines():
                line = line.replace("\n", "")
                if not line.strip():
                    continue
                parts = line.split(",")
                cpu = round(float(parts[1]), 2)
                mem = round(float(parts[2]), 2)
                data.append({"date": parts[0], "cpu": cpu, "mem": mem})
                cpu_samples.append(cpu)
                mem_samples.append(mem)
                self.analyzer.update_resources(cpu, mem)
        if cpu_samples:
            self.__cpu_average = "{:.1f}%".format(mean(cpu_samples))
            self.__cpu_peak = "{:.0f}%".format(max(cpu_samples))
            self.__mem_average = "{:.1f}%".format(mean(mem_samples))
            self.__mem_peak = "{:.0f}%".format(max(mem_samples))
        return data

    @staticmethod
    def __build_resource_svg(resource_data):
        if not resource_data:
            return ""
        n = len(resource_data)
        x0, x1 = 40.0, 550.0
        y_base, y_top = 130.0, 10.0
        w = x1 - x0
        h = y_base - y_top

        pts_cpu, pts_mem = [], []
        for i, s in enumerate(resource_data):
            x = x0 + (i / max(n - 1, 1)) * w
            pts_cpu.append((x, y_base - min(s["cpu"], 100) / 100.0 * h))
            pts_mem.append((x, y_base - min(s["mem"], 100) / 100.0 * h))

        def fmt(pts):
            return " ".join("{:.1f},{:.1f}".format(x, y) for x, y in pts)

        def poly(pts):
            closed = list(pts) + [(pts[-1][0], y_base), (pts[0][0], y_base)]
            return " ".join("{:.1f},{:.1f}".format(x, y) for x, y in closed)

        cpu_vals = [s["cpu"] for s in resource_data]
        peak_i = cpu_vals.index(max(cpu_vals))
        peak_x, peak_y = pts_cpu[peak_i]
        peak_val = cpu_vals[peak_i]

        def parse_dt(s):
            for fmt_str in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(s.strip(), fmt_str)
                except ValueError:
                    pass
            return None

        times = [parse_dt(s["date"]) for s in resource_data]
        n_labels = min(6, n)
        idxs = ([0] if n_labels <= 1
                else [round(i * (n - 1) / (n_labels - 1)) for i in range(n_labels)])
        x_labels = []
        for idx in idxs:
            lx = x0 + (idx / max(n - 1, 1)) * w
            t = times[idx]
            x_labels.append((lx, t.strftime("%H:%M:%S") if t else ""))

        parts = ['<svg viewBox="0 0 560 160" style="display:block;width:100%">']
        for y, dash in [(10, True), (40, True), (70, True), (100, True), (130, False)]:
            d = ' stroke-dasharray="3,3"' if dash else ""
            parts.append(
                f'<line x1="40" y1="{y}" x2="550" y2="{y}" '
                f'stroke="var(--border)" stroke-width="1"{d}/>')
        for y_lbl, pct in [(14, "100%"), (44, "75%"), (74, "50%"), (104, "25%"), (133, "0%")]:
            parts.append(
                f'<text x="36" y="{y_lbl}" text-anchor="end" fill="var(--ink-faint)" '
                f'font-size="9" font-family="\'IBM Plex Mono\',monospace">{pct}</text>')
        for lx, label in x_labels:
            parts.append(
                f'<text x="{lx:.0f}" y="148" text-anchor="middle" fill="var(--ink-faint)" '
                f'font-size="9" font-family="\'IBM Plex Mono\',monospace">{label}</text>')
        parts.append(
            f'<polygon points="{poly(pts_mem)}" fill="#34bff5" fill-opacity="0.07"/>')
        parts.append(
            f'<polyline points="{fmt(pts_mem)}" fill="none" stroke="#34bff5" '
            f'stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>')
        parts.append(
            f'<polygon points="{poly(pts_cpu)}" fill="var(--brand)" fill-opacity="0.09"/>')
        parts.append(
            f'<polyline points="{fmt(pts_cpu)}" fill="none" stroke="var(--brand)" '
            f'stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>')
        parts.append(
            f'<line x1="{peak_x:.1f}" y1="{min(peak_y + 5, y_base):.1f}" '
            f'x2="{peak_x:.1f}" y2="{y_base}" '
            f'stroke="var(--brand)" stroke-width="1" stroke-dasharray="2,3" opacity="0.35"/>')
        parts.append(
            f'<circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="3.5" fill="var(--brand)"/>')
        label_y = peak_y - 6
        near_right = peak_x > x0 + w * 0.72
        if near_right:
            label_x = peak_x - 5
            anchor = "end"
        else:
            label_x = peak_x + 5
            anchor = "start"
        parts.append(
            f'<text x="{label_x:.1f}" y="{label_y:.1f}" fill="var(--brand)" '
            f'text-anchor="{anchor}" '
            f'font-size="9" font-family="\'IBM Plex Mono\',monospace" '
            f'font-weight="600">{peak_val:.0f}% peak</text>')
        parts.append('</svg>')
        return "\n".join(parts)

    # ── Totals ────────────────────────────────────────────────────────────────

    def __build_totals(self, status_durations):
        t = self.test_totals
        total = t.get("total", 0)
        n_success = t.get(TestCategory.SUCCESS, 0)
        if total > 0 and n_success > 0:
            passing_rate = "{:.1f}%".format(n_success / total * 100)
        else:
            passing_rate = "0.0%"
        avg_dur = {}
        for status, durs in status_durations.items():
            avg_dur[status] = "{:.2f}s".format(mean(durs)) if durs else "—"
        return {
            "total": total,
            TestCategory.SUCCESS: t.get(TestCategory.SUCCESS, 0),
            TestCategory.FAIL: t.get(TestCategory.FAIL, 0),
            TestCategory.ERROR: t.get(TestCategory.ERROR, 0),
            TestCategory.IGNORE: t.get(TestCategory.IGNORE, 0),
            TestCategory.SKIP: t.get(TestCategory.SKIP, 0),
            TestCategory.CANCEL: t.get(TestCategory.CANCEL, 0),
            "passing_rate": passing_rate,
            "avg_dur": avg_dur,
        }

    # ── Bar data for stacked charts ────────────────────────────────────────────

    def __get_bar_data(self):

        def make_entry(label, metrics_dict):
            total = sum(metrics_dict.get(s, 0) for s in TestCategory.ALL)
            if total == 0:
                return None
            perf = metrics_dict.get("performance", [])
            avg_dur = "{:.2f}s".format(mean(perf)) if perf else "—"
            entry = {"label": label, "total": total, "avgDur": avg_dur}
            for s in TestCategory.ALL:
                entry[s] = metrics_dict.get(s, 0)
            return entry

        features = []
        for feat, comps in self.features.items():
            lbl = feat if feat is not None else "Not Defined"
            e = make_entry(lbl, comps["_totals_"])
            if e:
                features.append(e)

        components = []
        comp_agg = {}
        for feat, comps in self.features.items():
            for comp, metrics in comps.items():
                if comp == "_totals_":
                    continue
                if comp is None:
                    if None not in comp_agg:
                        comp_agg[None] = {k: list(v) if isinstance(v, list) else v
                                          for k, v in metrics.items()}
                    else:
                        for s in TestCategory.ALL:
                            comp_agg[None][s] = comp_agg[None].get(s, 0) + metrics.get(s, 0)
                        comp_agg[None]["performance"] = (
                            comp_agg[None].get("performance", []) + metrics.get("performance", []))
                else:
                    e = make_entry(comp, metrics)
                    if e:
                        components.append(e)
        if None in comp_agg:
            e = make_entry("Not Defined", comp_agg[None])
            if e:
                components.append(e)

        owners = []
        for owner, metrics in self.owners.items():
            if owner == "_totals_":
                continue
            lbl = owner if owner is not None else "Not Defined"
            e = make_entry(lbl, metrics)
            if e:
                owners.append(e)

        suites = []
        for suite_name, metrics in self.suites.items():
            if suite_name == "_totals_":
                continue
            e = make_entry(suite_name, metrics)
            if e:
                suites.append(e)

        tags = []
        for tag, metrics in self.tags.items():
            e = make_entry(tag, metrics)
            if e:
                tags.append(e)

        return {
            "features": features,
            "components": components,
            "owners": owners,
            "suites": suites,
            "tags": tags,
        }

    # ── Insights (plain text) ─────────────────────────────────────────────────

    def __get_plain_insights(self):
        insights = list(self.analyzer.structured_analysis)
        # Strip generic threading message; replaced below with richer analysis
        insights = [
            i for i in insights
            if not (isinstance(i, dict) and "multi-thread" in i.get("text", "").lower())
        ]
        if not self.analyzer.multi_threading_enabled:
            rich = self.__get_threading_insight()
            if rich:
                insights.append(rich)
        return insights

    def __get_threading_insight(self):
        tasks = self._thread_tasks
        if len(tasks) < 3:
            return None

        durations = [t["dur"] for t in tasks]
        serial = sum(durations)
        if serial <= 0:
            return None  # near-instant tests: nothing to gain from threads (and the math below divides by zero)

        def simulate(n):
            buckets = [0.0] * n
            for d in sorted(durations, reverse=True):
                idx = min(range(n), key=lambda i: buckets[i])
                buckets[idx] += d
            return max(buckets)

        candidates = []
        for n in range(2, min(len(tasks) + 1, 17)):
            est = simulate(n)
            candidates.append((n, est))
            if len(candidates) >= 2:
                prev = candidates[-2][1]
                if prev > 0 and (prev - est) / prev < 0.05:
                    break

        # Last candidate before diminishing returns triggered the break;
        # recommend the one before it if improvement was marginal.
        # used to divide by zero (crashing report generation) when an estimate rounded down to 0
        if len(candidates) >= 2 and candidates[-2][1] > 0 and \
                (candidates[-2][1] - candidates[-1][1]) / candidates[-2][1] < 0.05:
            rec_n, rec_est = candidates[-2]
        else:
            rec_n, rec_est = candidates[-1]

        speedup = serial / max(rec_est, 0.001)
        saved = serial - rec_est

        top_tests = sorted(tasks, key=lambda t: t["dur"], reverse=True)[:10]
        all_ids = list({t["id"] for t in tasks})

        return {
            "text": "Multi-threading could save ~{:.1f}s ({:.1f}× faster with {} threads).".format(
                saved, speedup, rec_n),
            "traceback": None,
            "test_ids": all_ids,
            "dialog": {
                "type": "threading",
                "serial_time": round(serial, 2),
                "recommended_threads": rec_n,
                "estimated_time": round(rec_est, 2),
                "speedup": round(speedup, 1),
                "time_saved": round(saved, 2),
                "test_count": len(tasks),
                "top_tests": [
                    {"id": t["id"], "name": t["name"], "suite": t["suite"],
                     "dur": round(t["dur"], 3)}
                    for t in top_tests
                ],
            },
        }

    # ── Table / detail data ────────────────────────────────────────────────────

    def __get_table_data(self):

        def _fmt_dur(seconds):
            return "{:.2f}s".format(seconds)

        def _fmt_ts(epoch):
            try:
                return datetime.fromtimestamp(epoch).strftime("%H:%M:%S")
            except Exception:
                return "—"

        def _str_param(val):
            if val is None:
                return None
            s = str(val)
            if s.startswith("<") and s.endswith(">"):
                s = "&lt;{}&gt;".format(s[1:-1])
            return s

        def _fail_or_error(phase_data, idx, tb):
            # by the recorded exception type - searching the traceback text for "AssertionError" mislabelled
            # errors whose message merely mentions an AssertionError
            exceptions = phase_data.get("exceptions", [])
            exception = exceptions[idx] if idx < len(exceptions) else None
            if exception is not None:
                return "Fail" if isinstance(exception, AssertionError) else "Error"
            return "Fail" if "AssertionError" in str(tb) else "Error"

        def _phase_detail(phase_data, idx):
            perf = phase_data.get("performance", [])
            tbs = phase_data.get("tracebacks", [])
            if idx >= len(perf) or perf[idx] is None:
                return {"status": "N/A", "trace": "N/A", "dur": "—"}
            dur_str = _fmt_dur(perf[idx]) if isinstance(perf[idx], (int, float)) else str(perf[idx])
            tb = tbs[idx] if idx < len(tbs) else None
            if tb is None:
                return {"status": "OK", "trace": "OK", "dur": dur_str}
            return {"status": _fail_or_error(phase_data, idx, tb), "trace": str(tb), "dur": dur_str}

        def _test_phase_detail(pd, idx):
            perf = pd.get("performance", [])
            tbs = pd.get("tracebacks", [])
            if idx >= len(perf):
                return {"status": "N/A", "trace": "N/A", "dur": "—"}
            dur_raw = perf[idx]
            dur_str = _fmt_dur(dur_raw) if isinstance(dur_raw, (int, float)) else str(dur_raw)
            tb = tbs[idx] if idx < len(tbs) else None
            if tb is None:
                return {"status": "OK", "trace": "OK", "dur": dur_str}
            return {"status": _fail_or_error(pd, idx, tb), "trace": str(tb), "dur": dur_str}

        def _convert_suite_metrics(raw):
            result = {}
            for dec in [DecoratorType.BEFORE_CLASS, DecoratorType.AFTER_CLASS,
                        DecoratorType.BEFORE_TEST, DecoratorType.AFTER_TEST]:
                d = raw.get(dec, {})
                perf = d.get("performance", [])
                tbs = d.get("tracebacks", [])
                excs = d.get("exceptions", [])
                executions = sum(1 for t in tbs if t != "N/A") if tbs else 0
                failures = sum(1 for e in excs if e is not None) if excs else 0
                if perf:
                    avg_v = "{:.2f}s".format(mean(perf))
                    med_v = "{:.2f}s".format(median(perf))
                    min_v = "{:.2f}s".format(min(perf))
                    max_v = "{:.2f}s".format(max(perf))
                else:
                    avg_v = med_v = min_v = max_v = "—"
                result[dec] = {
                    "avg": avg_v, "median": med_v, "min": min_v, "max": max_v,
                    "executions": executions, "failures": failures,
                }
            return result

        status_priority = [TestCategory.CANCEL, TestCategory.IGNORE, TestCategory.ERROR,
                           TestCategory.FAIL, TestCategory.SKIP, TestCategory.SUCCESS]

        def _priority_status(statuses):
            unique = set(statuses)
            if len(unique) == 1:
                return statuses[0]
            for s in status_priority:
                if s in unique:
                    return s
            return statuses[-1] if statuses else "unknown"

        def _get_copy(value):
            # deepcopy fails on e.g. an exception object holding a lock or socket - this used to return None and
            # the test silently disappeared from the report. Copy the structure and keep un-copyable leaves as is
            # (the report only reads them)
            try:
                return copy.deepcopy(value)
            except Exception:
                LogJunkie.debug("Metrics are not deep-copyable, copying structure only: {}"
                                .format(traceback.format_exc()))
                if isinstance(value, dict):
                    return {key: _get_copy(item) for key, item in value.items()}
                if isinstance(value, (list, tuple)):
                    return type(value)(_get_copy(item) for item in value)
                return value

        tests_data = []
        details_data = {}
        status_durations = {s: [] for s in TestCategory.ALL}

        for suite in self.aggregator.executed_suites:
            suite_raw_metrics = _get_copy(suite.metrics.get_metrics())
            suite_metrics_converted = _convert_suite_metrics(suite_raw_metrics) if suite_raw_metrics else {}
            module = suite.get_class_module()
            suite_name = suite.get_class_name()
            feature = suite.get_feature() or "Not Defined"
            tags_list = [t for t in (suite.get_tags() if hasattr(suite, "get_tags") else []) if t]

            for test in suite.get_test_objects():
                test_id = test.get_test_id()
                test_metrics_raw = _get_copy(test.metrics.get_metrics())
                if not test_metrics_raw:
                    continue

                component = test.get_component() or "Not Defined"
                owner = test.get_owner() or "Not Defined"
                test_name = test.get_function_name()
                test_tags = list(test.get_tags() or [])
                if not test_tags:
                    test_tags = tags_list

                all_statuses = []
                all_starts = []
                all_ends = []
                all_dur_floats = []
                variants = []

                for cp_str, cp_data in test_metrics_raw.items():
                    for tp_str, pd in cp_data.items():
                        if pd.get("status") is None:
                            continue

                        raw_perf = list(pd.get("performance", []))
                        all_dur_floats.extend(raw_perf)
                        if raw_perf:
                            self._thread_tasks.append({
                                "id": test_id,
                                "name": test_name,
                                "suite": suite_name,
                                "dur": sum(raw_perf),
                            })

                        start_ts = pd.get("start")
                        end_ts = pd.get("end")
                        if start_ts:
                            all_starts.append(start_ts)
                        if end_ts:
                            all_ends.append(end_ts)

                        self.analyzer.analyze(
                            test_id=test_id,
                            tracebacks=list(pd.get("tracebacks", [])),
                            performance=raw_perf,
                        )

                        # Accumulate duration per status for donut
                        v_status = pd.get("status", "")
                        for dur in raw_perf:
                            if v_status in status_durations:
                                status_durations[v_status].append(dur)

                        all_statuses.append(v_status)

                        # Build variant
                        params_total_raw = sum(raw_perf)
                        params_total_str = _fmt_dur(params_total_raw) if raw_perf else "—"

                        attempts = []
                        for i in range(len(raw_perf)):
                            bt_phase = _phase_detail(pd.get(DecoratorType.BEFORE_TEST, {}), i)
                            t_phase = _test_phase_detail(pd, i)
                            at_phase = _phase_detail(pd.get(DecoratorType.AFTER_TEST, {}), i)
                            attempts.append({
                                "n": i + 1,
                                "runtime": t_phase["dur"],
                                "beforeTest": bt_phase,
                                "test": t_phase,
                                "afterTest": at_phase,
                            })

                        variants.append({
                            "classParam": _str_param(pd.get("class_param")),
                            "testParam": _str_param(pd.get("param")),
                            "status": v_status,
                            "totalDuration": params_total_str,
                            "attempts": attempts,
                        })

                if not all_statuses:
                    continue

                final_status = _priority_status(all_statuses)
                total_dur = sum(all_dur_floats)
                duration_str = _fmt_dur(total_dur) if all_dur_floats else "—"
                dur_sec = round(total_dur, 3)

                started_str = _fmt_ts(min(all_starts)) if all_starts else "—"
                ended_str = _fmt_ts(max(all_ends)) if all_ends else "—"

                retries = sum(max(0, v.get("retry", 1) - 1)
                              for cp_d in test_metrics_raw.values()
                              for v in cp_d.values()
                              if v.get("status") is not None)

                variant_count = sum(
                    sum(1 for pd in cp_d.values() if pd.get("status") is not None)
                    for cp_d in test_metrics_raw.values()
                )

                test_entry = {
                    "id": test_id,
                    "suite": suite_name,
                    "test": test_name,
                    "feature": feature,
                    "component": component,
                    "owner": owner,
                    "tags": test_tags,
                    "started": started_str,
                    "ended": ended_str,
                    "duration": duration_str,
                    "durationSec": dur_sec,
                    "retries": retries,
                    "status": final_status,
                }
                if variant_count > 1:
                    test_entry["variantCount"] = variant_count
                tests_data.append(test_entry)

                details_data[test_id] = {
                    "module": module,
                    "suiteMetrics": suite_metrics_converted,
                    "variants": variants,
                }

        return {
            "tests_data": tests_data,
            "details_data": details_data,
            "status_durations": status_durations,
        }
