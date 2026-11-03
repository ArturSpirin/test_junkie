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
| `--traceback-limit` | Test Junkie's (3000) | characters of each traceback the run keeps |
| `--case named-300` | | 300 tests, all failing, 6 reruns |
| `--matrix` | | 1k/0%, 1k/30%, 5k/10%, 20k/30% (6 reruns, 40 frames) and `named-300` |
| `--pass` | `both` | `time`, `memory` or `both` |
| `--timeout` | 1800 | seconds per size, all passes together |
| `--out` | a temp dir, removed | keeps `OUT/<size>/report.html`, `report.xml` and `console.txt` |

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
