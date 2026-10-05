import os
import threading

from test_junkie.cli.cli_runner import CliRunner
from test_junkie.constants import Undefined
from test_junkie.debugger import LogJunkie

SUITE_SOURCE = """from test_junkie.decorators import Suite, test


@Suite()
class {name}:

    @test()
    def a_test(self):
        pass
"""


def _scan(source_dir):
    runner = CliRunner(sources=[str(source_dir)], ignore=[".git"], suites=None,
                       code_cov=False, cov_rcfile=None, guess_root=False, config=Undefined)
    runner.scan()
    return [suite.__name__ for suite in runner.suites]


def test_scan_finds_suites_in_leaf_directory(tmp_path):
    # suites in a directory with no subdirectories used to be missed on Linux/macOS -
    # the scanner globbed dirname(dir + "\\"), which is the parent dir unless "\" is the separator
    leaf = tmp_path / "suites" / "leaf"
    leaf.mkdir(parents=True)
    (leaf / "leaf_dir_scan_suite.py").write_text(SUITE_SOURCE.format(name="LeafDirScanSuite"))

    assert _scan(tmp_path / "suites") == ["LeafDirScanSuite"], \
        "Expected the suite in {} to be found".format(os.path.join("suites", "leaf"))


def test_scan_with_logging_enabled_does_not_deadlock(tmp_path):
    # tj run -v used to hang forever: the scanner held the shared @synchronized() lock while importing
    # suites, and LogJunkie took the same lock when @Suite logged during that import
    (tmp_path / "verbose_scan_suite.py").write_text(SUITE_SOURCE.format(name="VerboseScanSuite"))
    found = []
    LogJunkie.enable_logging(10)
    try:
        scan = threading.Thread(target=lambda: found.extend(_scan(tmp_path)), daemon=True)
        scan.start()
        scan.join(timeout=30)
    finally:
        LogJunkie.disable_logging()

    assert not scan.is_alive(), "Scan deadlocked with logging enabled"
    assert found == ["VerboseScanSuite"]
