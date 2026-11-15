import os
import stat

from test_junkie.decorators import Suite, test, beforeTest, afterTest
from test_junkie.shortcuts import skip

SEEN = []  # (who, path) for every temp_dir handed out


@Suite()
class TempDirSharedSuite:
    # beforeTest, the test and afterTest get the same directory

    @beforeTest()
    def before(self, temp_dir):
        SEEN.append(("before", temp_dir))
        assert list(temp_dir.iterdir()) == []  # new and empty
        (temp_dir / "made_in_before.txt").write_text("hello")

    @afterTest()
    def after(self, temp_dir):
        SEEN.append(("after", temp_dir))
        assert (temp_dir / "made_in_test.txt").read_text() == "world"

    @test()
    def shared(self, temp_dir):
        SEEN.append(("test", temp_dir))
        assert (temp_dir / "made_in_before.txt").read_text() == "hello"
        (temp_dir / "made_in_test.txt").write_text("world")


@Suite()
class TempDirResultsSuite:
    # the directory goes whatever the result

    @test()
    def passes(self, temp_dir):
        SEEN.append(("passes", temp_dir))
        (temp_dir / "f").write_text("x")

    @test()
    def fails(self, temp_dir):
        SEEN.append(("fails", temp_dir))
        (temp_dir / "f").write_text("x")
        assert False

    @test()
    def errors(self, temp_dir):
        SEEN.append(("errors", temp_dir))
        (temp_dir / "f").write_text("x")
        raise RuntimeError("boom")

    @test()
    def skips(self, temp_dir):
        SEEN.append(("skips", temp_dir))
        (temp_dir / "f").write_text("x")
        skip("not today")

    @test(parameters=[1, 2])
    def parameterized(self, parameter, temp_dir):
        SEEN.append(("parameterized", temp_dir))
        (temp_dir / "p{}".format(parameter)).write_text("x")

    @test()
    def keyword_only(self, *, temp_dir=None):
        SEEN.append(("keyword_only", temp_dir))
        assert temp_dir is not None

    @test()
    def read_only_file(self, temp_dir):
        SEEN.append(("read_only_file", temp_dir))
        locked = temp_dir / "sub" / "locked.txt"
        locked.parent.mkdir()
        locked.write_text("x")
        os.chmod(str(locked), stat.S_IREAD)


@Suite()
class TempDirBeforeTestFailsSuite:

    @beforeTest()
    def before(self, temp_dir):
        SEEN.append(("before", temp_dir))
        (temp_dir / "f").write_text("x")
        raise RuntimeError("setup broke")

    @test()
    def never_runs(self, temp_dir):
        SEEN.append(("test", temp_dir))


@Suite()
class TempDirRetrySuite:
    # a retry gets a new, empty directory

    @test(retry=2)
    def flaky(self, temp_dir):
        SEEN.append(("flaky", temp_dir))
        assert list(temp_dir.iterdir()) == []
        (temp_dir / "f").write_text("x")
        assert len([s for s in SEEN if s[0] == "flaky"]) == 2


@Suite()
class TempDirNotAskedSuite:
    # nothing names temp_dir: nothing is made

    @beforeTest()
    def before(self):
        pass

    @test()
    def plain(self):
        pass

    @test(parameters=[1])
    def with_param(self, parameter):
        pass


def run(suite):
    """
    :return: (SEEN, Aggregator)
    """
    from test_junkie.runner import Runner
    del SEEN[:]
    aggregator = Runner([suite], quiet=True).run()
    return list(SEEN), aggregator


def paths(seen, who):
    return [p for w, p in seen if w == who]
