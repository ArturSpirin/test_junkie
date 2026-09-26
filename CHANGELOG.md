# Changelog

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
