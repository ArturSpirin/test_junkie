# End-of-run stress harness

Times the three steps at the end of `Runner.run()` (`test_junkie/runner.py`), each on its own: the console summary
(`Console.finish`), the HTML report (`Reporter(...)` + `generate_html_report`) and the XML report
(`XmlReporter.create_xml_report`). It runs a generated run through `Runner` and wraps the runner's own calls, so it
measures the same code a user's run does. Generated names and messages only.

From the repo root:

```
python3.13 -m tests.stress.report_stress --tests 1000 --fail-rate 0.3 --reruns 6 --frames 40 --out OUT
```

| Option | Default | Meaning |
|---|---|---|
| `--tests` | 1000 | tests in the run, in suites of 100 |
| `--fail-rate` | 0.3 | share of tests (0-1) that fail on every attempt; half fail (`AssertionError`), half error |
| `--reruns` | 6 | reruns of each failing test (`@test(retry=reruns + 1)`) |
| `--frames` | 40 | distinct frames in each failure's traceback |
| `--skip-rate` | 0 | share of tests (0-1), from the non-failing ones, marked `@test(skip=True)` |
| `--traceback-limit` | Test Junkie's (3000) | characters of each traceback the run keeps |
| `--case named-300` | | 300 tests, all failing, 6 reruns |
| `--matrix` | | 1k/0%, 1k/30%, 5k/10%, 20k/30% (6 reruns, 40 frames) and `named-300` |
| `--pass` | `both` | `time`, `memory` or `both` |
| `--timeout` | 1800 | seconds per size, all passes together |
| `--out` | a temp dir, removed | keeps `OUT/<size>/report.html`, `report.xml`, `console.txt` and `expected.json` |

One line per size (these from 0.9a8, 2026-11-03):

```
1000 tests 0% fail/error 6 reruns 40 frames | run 0.08 s | console.finish 0.00 s 0.0 MB | html 0.06 s 11.9 MB (construct 0.01 s 0.2 MB + generate 0.05 s 11.9 MB) | xml 0.01 s 0.7 MB
2000 tests 30% fail/error 6 reruns 40 frames | run 55.04 s | console.finish 4.30 s | html - (construct 0.13 s + generate -) | xml - | DID NOT FINISH within 30 min (time pass stopped in html_generate), stopped after 1801 s
```

- `run` is the time from `Runner.run()` to the summary: the tests themselves, not an end-of-run step.
- Times come from the time pass; peak memory (`tracemalloc`, what the step itself allocated) from a separate memory
  pass with the same seed, so tracing doesn't slow the timed run. Each pass runs in its own process.
- The memory pass is much slower (`tracemalloc` traces every allocation; about 40x on the HTML report), so on large
  sizes it is the one most likely to reach the cap. A size over `--timeout` is stopped and reported as
  `DID NOT FINISH within N min (<pass> pass stopped)`, with whatever it measured before.
- The output files are the first pass's. The XML report appends to an existing file, so each pass writes fresh files.
- `tests/junkie_suites/stress_checks.py` runs a 20-test size in the normal suite to keep the harness working.

## Report correctness

`report_check.py` checks the reports one kept size folder holds against its `expected.json` (what was generated):

```
python3.13 -m tests.stress.report_check OUT/<size> [--browser] [--screenshot panel.png]
```

- **XML**: parsed with `xml.etree`, then validated with `xmlschema` against `xsd/junit-10.xsd`: the Jenkins xUnit
  plugin's JUnit schema, vendored unchanged from
  `https://github.com/jenkinsci/xunit-plugin/blob/0afa700702a6617f483cfd9407711976dc0bd74a/src/main/resources/org/jenkinsci/plugins/xunit/types/model/xsd/junit-10.xsd`
  (MIT). Errors are grouped by kind with counts, so the same kinds at every size mean nothing breaks with scale.
- **Counts**: tests, passed, failures, errors, skipped and reruns, from the generated run, the XML's `<testsuite>`
  attributes, the XML's elements, and the HTML page's data. A rerun is a run of a test after its first: in the XML a
  `rerunFailure`/`rerunError`/`flaky*` element, in the HTML the Retries column.
- **`--browser`**: opens the page in headless Chromium and times DOMContentLoaded, `load` (which waits on the page's
  Google Fonts stylesheet, so it includes the network), the table, filtering to failures and errors, scrolling to the
  last of them (mouse wheel), opening one, expanding its first attempt and wheeling its panel to the end. Timings
  are reported, not judged. `--offline` blocks every non-file request, so the times don't depend on the network;
  the small-size check always runs that way.
  Needs `pip install playwright==1.64.1 && python -m playwright install chromium` (CI does this on 3.13 only).
- `tests/junkie_suites/report_correctness_checks.py` runs a 40-test size (30% failing, 10% skipped, 2 reruns) in the
  normal suite. Checks that fail on a known bug are `xfail(strict=True)` on pytest and skipped with the task key on TJ.
