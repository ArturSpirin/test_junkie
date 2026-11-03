import logging
import re

from test_junkie.debugger import LogJunkie
from test_junkie.decorators import Suite, test
from test_junkie.runner import Runner


@Suite()
class EndOfRunPassingSuite:

    @test()
    def passes(self):
        pass


@Suite()
class EndOfRunFailingSuite:

    @test()
    def fails(self):
        assert False, "planned failure"


_TIME = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"


class _Capture(logging.Handler):

    def __init__(self):
        super().__init__(logging.INFO)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def end_of_run_lines(**reports):
    """Runs the two suites above with LogJunkie at INFO and returns the 'End of run:' log lines, in order."""
    logger = logging.getLogger("TestJunkieLogger")
    capture = _Capture()
    old_level = logger.level
    logger.addHandler(capture)
    logger.setLevel(logging.INFO)  # LogJunkie fixes the level at first use; set it so test order can't hide lines
    LogJunkie.enable_logging(logging.INFO)
    try:
        Runner([EndOfRunPassingSuite, EndOfRunFailingSuite]).run(**reports)
    finally:
        LogJunkie.disable_logging()
        logger.removeHandler(capture)
        logger.setLevel(old_level)
    return [message for message in capture.messages if message.startswith("End of run:")]


def check_lines(lines, steps):
    """Asserts lines are a start and a finish line per step, in order, each timed."""
    assert len(lines) == 2 * len(steps), lines
    for index, step in enumerate(steps):
        start, finish = lines[2 * index], lines[2 * index + 1]
        assert re.fullmatch(r"End of run: {} started at {}".format(re.escape(step), _TIME), start), start
        assert re.fullmatch(r"End of run: {} finished at {} in \d+\.\d{{3}}s".format(re.escape(step), _TIME),
                            finish), finish
