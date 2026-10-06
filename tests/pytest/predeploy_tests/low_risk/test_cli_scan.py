import threading

from test_junkie.debugger import LogJunkie
from tests.junkie_suites import cli_scan_samples
from tests.junkie_suites.cli_scan_samples import SAMPLES


def test_scan_finds_suites_in_leaf_directory(tmp_path):
    # suites in a directory with no subdirectories used to be missed on Linux/macOS -
    # the scanner globbed dirname(dir + "\\"), which is the parent dir unless "\" is the separator
    leaf = tmp_path / "suites" / "leaf"
    leaf.mkdir(parents=True)
    (leaf / "a_plain.py").write_text(SAMPLES["a_plain.py"][0])

    assert cli_scan_samples.scan(tmp_path / "suites") == ["ScanPlain"]


def test_scan_with_logging_enabled_does_not_deadlock(tmp_path):
    # tj run -v used to hang forever: the scanner held the shared @synchronized() lock while importing
    # suites, and LogJunkie took the same lock when @Suite logged during that import
    (tmp_path / "a_plain.py").write_text(SAMPLES["a_plain.py"][0])
    found = []
    LogJunkie.enable_logging(10)
    try:
        scan = threading.Thread(target=lambda: found.extend(cli_scan_samples.scan(tmp_path)), daemon=True)
        scan.start()
        scan.join(timeout=30)
    finally:
        LogJunkie.disable_logging()

    assert not scan.is_alive(), "Scan deadlocked with logging enabled"
    assert found == ["ScanPlain"]


def test_scan_finds_suites_in_every_style(tmp_path):
    # the scanner used to find suites with regexes and silently skipped base classes, trailing comments,
    # multi-line imports and module/import aliases - it must find all of them, in file order, and must not
    # import a file that never applies @Suite()
    cli_scan_samples.write_samples(str(tmp_path))

    assert cli_scan_samples.scan(tmp_path) == cli_scan_samples.EXPECTED_SUITES


def test_scan_does_not_register_a_suite_twice_for_overlapping_sources(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "a_plain.py").write_text(SAMPLES["a_plain.py"][0])

    assert cli_scan_samples.scan(tmp_path, nested, nested / "a_plain.py") == ["ScanPlain"]
