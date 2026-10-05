import os
import shutil
import tempfile
import threading

from test_junkie.debugger import LogJunkie
from test_junkie.decorators import Suite, test, beforeTest, afterTest
from tests.junkie_suites import cli_scan_samples
from tests.junkie_suites.cli_scan_samples import SAMPLES


def _write(path, file_name):
    with open(os.path.join(path, file_name), "w") as doc:
        doc.write(SAMPLES[file_name][0])


@Suite()
class CliScanSuite:

    @beforeTest()
    def before_test(self):
        self.root = tempfile.mkdtemp()

    @afterTest()
    def after_test(self):
        shutil.rmtree(self.root, ignore_errors=True)

    @test()
    def scan_finds_suites_in_leaf_directory(self):
        leaf = os.path.join(self.root, "suites", "leaf")
        os.makedirs(leaf)
        _write(leaf, "a_plain.py")
        assert cli_scan_samples.scan(os.path.join(self.root, "suites")) == ["ScanPlain"]

    @test()
    def scan_with_logging_enabled_does_not_deadlock(self):
        _write(self.root, "a_plain.py")
        found = []
        LogJunkie.enable_logging(10)
        try:
            scan = threading.Thread(target=lambda: found.extend(cli_scan_samples.scan(self.root)), daemon=True)
            scan.start()
            scan.join(timeout=30)
        finally:
            LogJunkie.disable_logging()
        assert not scan.is_alive(), "Scan deadlocked with logging enabled"
        assert found == ["ScanPlain"]

    @test()
    def scan_finds_suites_in_every_style(self):
        cli_scan_samples.write_samples(self.root)
        assert cli_scan_samples.scan(self.root) == cli_scan_samples.EXPECTED_SUITES

    @test()
    def scan_does_not_register_a_suite_twice_for_overlapping_sources(self):
        nested = os.path.join(self.root, "nested")
        os.makedirs(nested)
        _write(nested, "a_plain.py")
        assert cli_scan_samples.scan(self.root, nested, os.path.join(nested, "a_plain.py")) == ["ScanPlain"]
