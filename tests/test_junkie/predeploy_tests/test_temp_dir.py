import os
from pathlib import Path
from unittest import mock

from test_junkie.decorators import Suite, test
from test_junkie.tempdir import TempDir
from tests.junkie_suites import TempDirSuites as fixture
from tests.junkie_suites.TempDirSuites import TempDirSharedSuite, TempDirResultsSuite, \
    TempDirBeforeTestFailsSuite, TempDirRetrySuite, TempDirNotAskedSuite, TempDirSkipAfterTestSuite


@Suite()
class TempDirTestSuite:

    @test()
    def before_test_test_and_after_test_share_one_directory(self):
        seen, aggregator = fixture.run(TempDirSharedSuite)
        assert [w for w, _ in seen] == ["before", "test", "after"]
        assert len(set(p for _, p in seen)) == 1
        assert isinstance(seen[0][1], Path)
        assert aggregator.get_basic_report()["tests"]["success"] == 1

    @test()
    def the_directory_is_removed_after_the_test(self):
        seen, _ = fixture.run(TempDirSharedSuite)
        assert not os.path.exists(str(seen[0][1]))

    @test()
    def the_directory_is_removed_whatever_the_result(self):
        seen, aggregator = fixture.run(TempDirResultsSuite)
        tests = aggregator.get_basic_report()["tests"]
        assert (tests["total"], tests["success"], tests["fail"], tests["error"], tests["skip"]) == (8, 5, 1, 1, 1)
        assert len(seen) == 8
        assert [p for _, p in seen if os.path.exists(str(p))] == []

    @test()
    def each_parameter_gets_its_own_directory(self):
        seen, _ = fixture.run(TempDirResultsSuite)
        parameterized = fixture.paths(seen, "parameterized")
        assert len(parameterized) == 2
        assert parameterized[0] != parameterized[1]

    @test()
    def a_keyword_only_temp_dir_gets_the_path(self):
        seen, _ = fixture.run(TempDirResultsSuite)
        assert isinstance(fixture.paths(seen, "keyword_only")[0], Path)

    @test()
    def a_read_only_file_does_not_stop_the_removal(self):
        seen, _ = fixture.run(TempDirResultsSuite)
        assert not os.path.exists(str(fixture.paths(seen, "read_only_file")[0]))

    @test()
    def the_directory_is_removed_when_before_test_fails(self):
        seen, aggregator = fixture.run(TempDirBeforeTestFailsSuite)
        assert [w for w, _ in seen] == ["before"]
        assert not os.path.exists(str(seen[0][1]))
        assert aggregator.get_basic_report()["tests"]["error"] == 1

    @test()
    def after_test_gets_the_directory_after_a_runtime_skip(self):
        seen, aggregator = fixture.run(TempDirSkipAfterTestSuite)
        assert [w for w, _ in seen] == ["test", "after"]
        assert seen[0][1] == seen[1][1]
        assert not os.path.exists(str(seen[0][1]))
        assert aggregator.get_basic_report()["tests"]["skip"] == 1

    @test()
    def a_retry_gets_a_new_empty_directory(self):
        seen, aggregator = fixture.run(TempDirRetrySuite)
        flaky = fixture.paths(seen, "flaky")
        assert len(flaky) == 2
        assert flaky[0] != flaky[1]
        assert [p for p in flaky if os.path.exists(str(p))] == []
        assert aggregator.get_basic_report()["tests"]["success"] == 1

    @test()
    def nothing_is_made_when_no_one_asks(self):
        with mock.patch("test_junkie.tempdir.tempfile.mkdtemp") as mkdtemp:
            _, aggregator = fixture.run(TempDirNotAskedSuite)
        assert mkdtemp.call_count == 0
        assert aggregator.get_basic_report()["tests"]["success"] == 2

    @test()
    def a_failed_removal_only_warns(self):
        scratch = TempDir()
        path = scratch.path()
        try:
            with mock.patch("test_junkie.tempdir.shutil.rmtree", side_effect=OSError("in use")), \
                    mock.patch("test_junkie.tempdir.LogJunkie.warn") as warn:
                scratch.remove()
            assert warn.call_count == 1
            assert str(path) in warn.call_args[0][0]
        finally:
            os.rmdir(str(path))

    @test()
    def remove_does_nothing_when_never_made(self):
        with mock.patch("test_junkie.tempdir.shutil.rmtree") as rmtree:
            TempDir().remove()
        assert rmtree.call_count == 0
