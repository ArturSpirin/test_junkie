# Changelog

## 0.9a8
- A listener that raises no longer ends its suite: the rest of the suite runs, each listener error is listed under Problems and the run still fails at the end with `TestListenerError`
- Tests a suite never got to, because it ended early (a test calling `sys.exit()`, say), are reported as ignored instead of being left out of the summary and reports
- Logs from a logger with `propagate = False` are captured again; they were dropped instead of being shown for tests that didn't pass
- The header shows a test count that includes parameter functions as an estimate, e.g. `16+ tests`

## 0.9a7
- `tj run --rerun FILE` runs again only what didn't pass in a `--json-report`, down to the parameter. `Runner.run(rerun=...)` takes the report or a `Rerun`, which can be subclassed to match parameters another way

## 0.9a6
- New `tj run` console output: a header, a progress bar per suite, a Problems section and a summary table
- Tracebacks in the console are readable again: they printed as one escaped line on Python 3. Every run of a retried test is listed, identical runs share one traceback, and Test Junkie's own frames are left out
- What tests print and log is captured and only shown for tests that didn't pass. `--no-capture` shows it live (needed for `breakpoint()`)
- New `-p` / `--per-test` prints one line per test. `-q` now prints only the problems and a result line, and `Runner.run(quiet=True)` prints nothing
- Ctrl+C cancels a run cleanly: nothing new starts and nothing is retried, running tests finish, cleanup hooks and reports still run, exit code 12. A second Ctrl+C stops immediately with exit code 130
- Fixed Ctrl+C being ignored on Windows until the running test threads finished
- `Runner.cancel()` now also stops retries of a test that is already running
- A suite that is skipped, ignored or cancelled as a whole counts its tests in the summary. A suite ignored as a whole (e.g. bad suite parameters) now makes `tj run` exit 1
- New `tj audit` output: a block per suite/owner/feature/component/tag with its share of all tests, missing metadata marked, and a Gaps section. `--by-features` and `--by-components` now work, and filters list the matching tests
- New `tj config` output: `show --all` groups the settings, `update` shows old and new values and how to undo, `restore` shows what was cleared
- `tj run` shows when a saved config is used, where it is and which settings it applied
- `-p` / `--per-test` and `--no-capture` can be saved with `tj config update`
- Fixed `--guess-root` giving up when the source path is relative (`tj run -s tests --guess-root`)
- `tj run -m` charts CPU and memory after the summary, with every test as a dot on the same timeline and the suites under it; threaded runs also show how many tests ran at once. Resources are sampled every 0.25s instead of every second
- Fixed `tj run -m` being ignored: resources were only monitored when `-m` was saved with `tj config update`
- `tj config` and `tj audit` errors say what to type instead and exit with code 120 (`tj config update`, `tj config show` and `tj audit` with nothing to do used to exit 0); `tj config show` with no options now asks which settings instead of printing the whole file
- CLI options use dashes, the same in every command: `--tags-any`/`-k`, `--tags-all`/`-l`, `--skip-tags-any`/`-g`, `--skip-tags-all`/`-j`, `--test-multithreading-limit`, `--html-report` etc. The old names (`--run_on_match_any`, `--test_multithreading_limit`, ...) still work but are no longer listed in `-h`
- `tj audit` tag filters now match `tj run`: `-l` means tests with *all* the tags (it was "any" in `tj audit`), `-k` any of them; `--tags` still works as "any"
- A project config: `tj.cfg` (created with `tj config update ... --config ./tj.cfg`) or a `[tool.test_junkie]` table in `pyproject.toml` (read-only, Python 3.11+ or with `tomli`) is found from the current folder up and used instead of the user config. `tj run` with no `-s` in a project uses its saved sources, and the project folder is put on the import path if a suite import fails
- `-t` / `--tests` takes `Suite.test` names and patterns like `login_*`; `-x` takes patterns like `Legacy*`
- `--seed N` repeats a `TestOrder.RANDOM` order; the header always prints the seed that was used
- `--retry N` and `--no-retry` override every test's `retry=` for one run
- `--json-report FILE`: results as JSON, every run of every test with its error. `--html-report`, `--xml-report` and `--json-report` also take a folder
- In GitHub Actions, `tj run` prints an `::error` annotation per failed test, pointing at the failing line
- `tj audit --json` for scripts, and `tj audit --fail-on-gaps [owners,tags,...]` exits 1 when tests are missing that metadata (for CI)
- `tj version` shows the installed package, the config in use and the docs link. `tj` with no command, or an unknown one, exits 120 with the commands to use
- `TestOrder.RANDOM` with the same seed gives the same order in repeated runs within one process (it shuffled the previous run's order)
- `retry_on` and `no_retry_on` also match subclasses of the listed exceptions (they matched the exact type only, so `retry_on=[requests.exceptions.Timeout]` never retried a `ReadTimeout`)
- Smaller install despite the above (849 KB → 844 KB): the HTML report's page ships as package data, the CLI options are defined once

## 0.9a5
- Fixed `monitor_resources=True` leaving a `.resources_*` temp file behind after short runs: the monitor thread could re-create it after cleanup
- Fixed a `tag_config` that isn't a dict (e.g. a list) crashing with `AttributeError` instead of the intended `ConfigError`
- Fixed `tj run`/`tj audit` mixing up suite files that share a file name in different folders (audit merged their suites into one), and a suite file named like an existing module (e.g. `json.py`) replacing that module for the whole run - the HTML report crashed with `module 'json' has no attribute 'dumps'`
- Fixed a failing run (for example a broken custom listener) exiting without the console summary or the HTML/XML reports - they are now written first, then the error is raised
- Every run is ~200ms faster: removed a fixed sleep after the suite queue was processed
- Parallel runs no longer poll every 200ms (1s for prioritized suites) for a free thread or a lifted restriction - waiting suites and tests start as soon as a thread finishes
- `import test_junkie` is ~2x faster (~85ms → ~35ms): the HTML reporter, the CLI/colorama and multiprocessing load only when needed, and the version comes from `test_junkie.__version__` instead of `importlib.metadata`
- Smaller install (656 KB → 621 KB): the HTML report's CSS and JS ship as package data instead of Python strings that were installed twice (source + .pyc)
- XML report is written once at the end of a run instead of being rewritten to disk after every test
- Faster event dispatch: listener hooks your `Listener` doesn't override are skipped, and function signatures are inspected once instead of several times per test
- Fixed run time growing quadratically with suite size since 0.9a0 (1,000 tests: ~55s → ~2s): `Rules` hooks no longer deep-copy the whole suite per test, and hooks a `Rules` subclass doesn't override are skipped

## 0.9a4
- Fixed HTML report generation crashing with `ZeroDivisionError` for runs without threading that have 3+ near-instant tests
- Fixed a test whose exception can't be deep-copied (e.g. it holds a lock or socket) disappearing from the HTML report
- Fixed `tj config update` failing on values containing `%` (e.g. report paths)
- Fixed failed `tj config` commands exiting with code 0; an unknown `tj config` sub-command now exits 120
- Removed unreachable CLI error handling

## 0.9a3
- A malformed `tag_config` now raises a clear `ConfigError` instead of a bare `TypeError`
- Fixed `TestObject.get_suite_id()` returning the previous suite's id
- Fixed `Runner.cancel()` during a run raising `TypeError` for the remaining tests instead of cancelling them
- Fixed listener events `on_before_group_failure` / `on_before_group_error` never firing when a `@beforeGroup` failed
- Fixed `tj audit` ignoring `-x/--suites`, counting tests excluded by `--no-*` filters, and `--no-test-meta` checking the suite's meta instead of the test's
- Fixed `tj run` / `tj audit` silently skipping suites that inherit from a base class, have a comment on the class line, use multi-line or aliased imports, or `@module.Suite()`
- Fixed `tj run` / `tj audit` counting the same suite more than once when sources overlap (#25)
- Fixed every `tj run` crashing after `tj config update --html_report report.html` (or any `--xml_report`/path without a drive)
- Fixed a saved `guess_root=False` in the config being treated as enabled
- Fixed `@beforeGroup` / `@afterGroup` not running for any `Runner` after the first one in the same process
- Fixed a second `run()` on the same `Runner` running no tests, and `run()` arguments leaking into the next `run()`
- Fixed suite retries running `@beforeClass` without `@afterClass`, and setting up suite parameters that had nothing to retry
- Suite retries now rerun failed tests in their original order
- Fixed a race when suite- and test-level threading are both on (`cannot join thread before it is started`) that made suites stop part-way; parallel bookkeeping is now locked and reset per run, and each suite only waits for its own tests before `@afterClass`
- HTML report: escape suite/test names, owners, components and tags (a `<` in any of them broke the layout); label an attempt Fail vs Error by its exception type instead of searching the traceback text
- Removed unused legacy HTML-report insight code; faster traceback similarity checks
- Fixed errors inside suite/test threads (e.g. a failing custom listener) being swallowed: `run()` returned normally and the affected tests disappeared from the results. `run()` now raises them, same as without threads
- Added `TEST_JUNKIE_HOME` env var to relocate Test Junkie's config and temp files; the test suite now uses it so it never touches a developer's real config
- Fixed debug log reporting a setting as coming from KWARGS when it wasn't passed (#45, thanks @etaixiee)

## 0.9a2
- Added `@Suite(order=)` — control test execution order per suite via `TestOrder.ALPHABETICAL`, `TestOrder.RANDOM`, `TestOrder.PRIORITY_ASC`, or `TestOrder.PRIORITY_DESC`
- Added `TestOrder` constants class to `test_junkie.constants`
- Added `SuiteObject.get_order()` accessor
- Added full test coverage for all four ordering modes including regression guard for default behavior
- Added `shortcuts.skip(reason=None)` — raise a runtime skip from within a test body; fires `on_skip` event, counts as skip in all reports, does not retry
- Added `shortcuts.SkipTest` exception class
- Improved error messages across builder, runner, objects, parallels, and settings
- CLI now exits with code 1 on failures, errors, ignored tests, or when no tests ran
- Fixed `python -m test_junkie` doing nothing (entry point was defined but never called)
- Fixed `tj run -s <dir>` on Linux/macOS missing suites in directories without subdirectories
- Fixed `tj run -v` hanging forever while scanning for suites
- Tests are no longer included in the published wheel
- CI now combines coverage from both test paths (including CLI subprocesses) and uploads it to Codecov

## 0.9a0
- Fix for KeyError: None during report generation (#44)
- Fix for re-running the same suite with different tags reusing stale results (#43)
- Fixed a thread lock in runner.py that was never actually shared between calls
- Fixed SuiteObject/TestObject deepcopy returning self instead of a real copy
- Fixed a few race conditions in parallels.py
- Fixed get_number_of_actual_retries() looking up the wrong key
- Report/resource-monitor cleanup failures now print a warning instead of failing silently
- Fixed meta.py occasionally picking up the wrong test's metadata
- Cleaned up wildcard import in cli_config.py
- Dropped Python 2.7 support - removed the compat shims and legacy backport deps
- Now supports Python 3.9 through 3.14
- Replaced dead Travis CI with GitHub Actions, testing across all supported Python versions
- Bumped pytest and a few transitive deps to close known Snyk vulnerabilities
- README cleanup: dropped dead badges, added a features list, license badge, changelog link
- Fixed CI actually failing on 3.12/3.13/3.14 - pkg_resources isn't available there anymore
- Deleted the 6 stale snyk-fix branches now that they're consolidated
- Added a real publish pipeline: tag push -> TestPyPI -> smoke test -> PyPI, no stored credentials
