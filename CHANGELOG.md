# Changelog

## 0.9a3
- Fixed `tj run` / `tj audit` silently skipping suites that inherit from a base class, have a comment on the class line, use multi-line or aliased imports, or `@module.Suite()`
- Fixed `tj run` / `tj audit` counting the same suite more than once when sources overlap (#25)
- Fixed every `tj run` crashing after `tj config update --html_report report.html` (or any `--xml_report`/path without a drive)
- Fixed a saved `guess_root=False` in the config being treated as enabled
- Fixed `@beforeGroup` / `@afterGroup` not running for any `Runner` after the first one in the same process
- Fixed a second `run()` on the same `Runner` running no tests, and `run()` arguments leaking into the next `run()`
- Fixed suite retries running `@beforeClass` without `@afterClass`, and setting up suite parameters that had nothing to retry
- Suite retries now rerun failed tests in their original order
- Fixed a race when suite- and test-level threading are both on (`cannot join thread before it is started`) that made suites stop part-way; parallel bookkeeping is now locked and reset per run, and each suite only waits for its own tests before `@afterClass`
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
