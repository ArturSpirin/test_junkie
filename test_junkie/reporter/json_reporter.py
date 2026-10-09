import json
import os

import test_junkie
from test_junkie.constants import TestCategory
from test_junkie.metrics import is_flaky
from test_junkie.params import param_key


def _error(exception):
    return None if exception is None else "{}: {}".format(type(exception).__name__, exception).split("\n")[0]


def write_json_report(path, aggregator, runtime, seed=None):
    """
    tj run --json-report FILE: totals, then every suite and test result, with each run of a retried test
    """
    suites = []
    for suite in aggregator.executed_suites:
        tests = []
        for test in suite.get_test_objects():
            for class_param, by_param in test.metrics.get_metrics().items():
                for param, data in by_param.items():
                    if data.get("status") is None:
                        continue
                    exceptions = data.get("exceptions") or []
                    retried = {r["run"]: r for r in test.metrics.get_retries(data.get("param"), data.get("class_param"))}
                    entry = {
                        "name": test.get_function_name(),
                        "parameter": None if data.get("param") is None else param_key(data.get("param")),
                        "suite_parameter": None if data.get("class_param") is None else param_key(data.get("class_param")),
                        "status": data["status"],
                        "flaky": is_flaky(data),
                        "runs": [{"status": status,
                                  "runtime": round(runtime_, 4) if runtime_ is not None else None,
                                  "error": _error(exceptions[index] if index < len(exceptions) else None),
                                  "retry": retried.get(index + 1)}
                                 for index, (status, runtime_) in enumerate(zip(data.get("statuses") or [],
                                                                                data.get("performance") or []))]}
                    waits = test.metrics.get_conflict_waits(data.get("class_param"))
                    if waits:
                        entry["conflict_waits"] = waits
                    tests.append(entry)
        suites.append({"name": suite.get_class_name(), "module": suite.get_class_module(),
                       "status": suite.metrics.get_metrics().get("status"),
                       "runtime": round(suite.get_runtime() or 0, 4), "tests": tests})
    totals = aggregator.get_basic_report()["tests"]
    report = {"test_junkie": test_junkie.__version__, "runtime": round(runtime, 4), "seed": seed,
              "totals": {status: totals.get(status, 0) for status in ["total"] + TestCategory.ALL}, "suites": suites}
    folder = os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(path, "w", encoding="utf-8") as doc:
        json.dump(report, doc, indent=1)
