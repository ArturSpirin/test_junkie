import os
import pprint
import re

from test_junkie.constants import CliConstants
from test_junkie.runner import Runner
from test_junkie.cli.cli_config import Config
from tests.QualityManager import QualityManager
from tests.cli.CliTestSuite import AuthApiSuite, ShoppingCartSuite, NewProductsSuite
from tests.cli.Cmd import Cmd

ROOT = __file__.split("{0}tests".format(os.sep))[0]
EXE = ROOT + "{0}test_junkie{0}cli{0}cli.py".format(os.sep)
TESTS = ROOT + "{0}tests{0}cli".format(os.sep)


def test_help():

    commands = [['python3', EXE, '-h'],
                ['python3', EXE, 'run', '-h'],
                ['python3', EXE, 'audit', '-h'],
                ['python3', EXE, 'config', '-h'],
                ['python3', EXE, 'version', '-h']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception".format(cmd, output)


def test_module_entry_point():

    output = _plain(Cmd.run(['python3', '-m', 'test_junkie', 'version']))  # colored in CI
    assert any("Test Junkie " in line for line in output), \
        "python -m test_junkie produced no output: {}".format(output)


def test_sub_command_help():

    commands = [['python3', EXE, 'audit', 'features', '-h'],
                ['python3', EXE, 'audit', 'tags', '-h'],
                ['python3', EXE, 'audit', 'components', '-h'],
                ['python3', EXE, 'audit', 'owners', '-h'],
                ['python3', EXE, 'audit', 'suites', '-h'],
                ['python3', EXE, 'config', 'update', '-h'],
                ['python3', EXE, 'config', 'show', '-h'],
                ['python3', EXE, 'config', 'restore', '-h']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def test_incomplete_inputs():

    commands = [
                ['python3', EXE, 'config'],
                ['python3', EXE, 'config', 'update'],
                ['python3', EXE, 'config', 'restore'],
                ['python3', EXE, 'config', 'show'],
                ['python3', EXE, 'audit'],
                ['python3', EXE, 'version']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def _plain(output):
    """
    Cmd.run() lines are the repr of the raw bytes: strip color codes (on in CI, where GITHUB_ACTIONS is set)
    """
    return [re.sub(r"\\x1b\[[0-9;]*m", "", line) for line in output]


def test_config_update():

    commands = [['python3', EXE, 'config', 'update', '--test_multithreading_limit', '10'],
                ['python3', EXE, 'config', 'update', '--suite_multithreading_limit', '10'],
                ['python3', EXE, 'config', 'update', '--features', 'feat'],
                ['python3', EXE, 'config', 'update', '--components', 'comp'],
                ['python3', EXE, 'config', 'update', '--owners', 'own'],
                ['python3', EXE, 'config', 'update', '--monitor_resources'],
                ['python3', EXE, 'config', 'update', '--html_report', '/test/path/for/html'],
                ['python3', EXE, 'config', 'update', '--xml_report', '/test/path/for/xml'],
                ['python3', EXE, 'config', 'update', '--run_on_match_all', '1000'],
                ['python3', EXE, 'config', 'update', '--run_on_match_any', '2000'],
                ['python3', EXE, 'config', 'update', '--skip_on_match_all', '3000'],
                ['python3', EXE, 'config', 'update', '--skip_on_match_any', '4000'],
                ]
    for cmd in commands:
        output = _plain(Cmd.run(cmd))
        prop = cmd[4].replace("--", "")
        value = cmd[5] if len(cmd) == 6 else "on"
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        assert "SAVED" in output[0], output
        assert any(prop in line and line.rstrip("'").endswith(value) for line in output), \
            "Command: {} did not update property: {} to value: {}. {}".format(cmd, prop, value, output)


def test_config_restore():

    commands = [['python3', EXE, 'config', 'restore', '--test_multithreading_limit'],
                ['python3', EXE, 'config', 'restore', '--suite_multithreading_limit'],
                ['python3', EXE, 'config', 'restore', '--features'],
                ['python3', EXE, 'config', 'restore', '--components'],
                ['python3', EXE, 'config', 'restore', '--owners'],
                ['python3', EXE, 'config', 'restore', '--monitor_resources'],
                ['python3', EXE, 'config', 'restore', '--html_report'],
                ['python3', EXE, 'config', 'restore', '--xml_report'],
                ['python3', EXE, 'config', 'restore', '--run_on_match_all'],
                ['python3', EXE, 'config', 'restore', '--run_on_match_any'],
                ['python3', EXE, 'config', 'restore', '--skip_on_match_all'],
                ['python3', EXE, 'config', 'restore', '--skip_on_match_any'],
                ]
    for cmd in commands:
        output = _plain(Cmd.run(cmd))
        prop = cmd[4].replace("--", "")
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        assert "RESTORED" in output[0] and "1 setting to its default" in output[0], output
        assert any(prop in line for line in output[1:]), "Command: {} did not restore: {}".format(cmd, prop)


def _blocks(output):
    """
    :return: DICT of block title -> number of tests, for a tj audit view
    """
    blocks = {}
    for line in output:
        match = re.match(r"^(?:b')?(\S.*?) {2,}(\d+) tests? ", line)
        if match and not match.group(1).startswith("Test Junkie"):
            blocks[match.group(1)] = int(match.group(2))
    return blocks


def _audit(cmd):
    output = _plain(Cmd.run(cmd))
    for line in output:
        assert "Traceback (most recent call last)" not in line, "Command: {} produced exception. {}".format(cmd, output)
        assert "ERROR" not in line, output
    return output, _blocks(output)


def test_audit_by_owner():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    output, blocks = _audit(['python3', EXE, 'audit', 'owners', '-s', TESTS])
    assert blocks.get("Victor") == 4 and blocks.get("Mike") == 7 and blocks.get("George") == 5, (blocks, output)
    for row in ("suites", "features", "components", "tags"):
        assert any(line.startswith("  " + row + " ") for line in output), (row, output)
    output, blocks = _audit(['python3', EXE, 'audit', 'owners', '-s', TESTS, '-o', 'Mike'])
    assert list(blocks) == ["Mike"], (blocks, output)
    assert any("filters  owners Mike" in line for line in output), output
    assert any(line.startswith("  tests ") for line in output), output  # a filter lists the tests


def test_audit_by_suite():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    output, blocks = _audit(['python3', EXE, 'audit', 'suites', '-s', TESTS])
    assert blocks == {"AuthApiSuite": 6, "ShoppingCartSuite": 5, "NewProductsSuite": 5}, (blocks, output)
    output, blocks = _audit(['python3', EXE, 'audit', 'suites', '-s', TESTS, '-o', 'Mike'])
    assert "Victor" not in " ".join(output) and "George" not in " ".join(output), output
    assert any(line.startswith("  owners ") and "Mike" in line for line in output), output


def test_audit_by_tags():
    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    output, blocks = _audit(['python3', EXE, 'audit', 'tags', '-s', TESTS])
    assert blocks.get("api") == 6 and blocks.get("sso") == 2, (blocks, output)
    output, blocks = _audit(['python3', EXE, 'audit', 'tags', '-s', TESTS, '-l', 'sso'])
    assert blocks.get("sso") == 2 and any("2 tests" in line and "sso" in line for line in output), (blocks, output)


def test_audit_by_features():
    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    output, blocks = _audit(['python3', EXE, 'audit', 'features', '-s', TESTS])
    assert any(line.startswith("  owners ") and "Mike 5" in line for line in output), output
    output, blocks = _audit(['python3', EXE, 'audit', 'features', '-s', TESTS, '-f', 'Store'])
    assert list(blocks) == ["Store"], (blocks, output)
    assert any("Mike 5" in line for line in output) and any("George 5" in line for line in output), output


def test_audit_by_components():
    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    output, blocks = _audit(['python3', EXE, 'audit', 'components', '-s', TESTS])
    assert blocks.get("Auth") == 6 and blocks.get("Admin") == 5, (blocks, output)
    output, blocks = _audit(['python3', EXE, 'audit', 'components', '-s', TESTS, '-c', 'Admin'])
    assert list(blocks) == ["Admin"], (blocks, output)


def test_bad_inputs():

    commands = [['python3', EXE, 'run'],
                ['python3', EXE, 'audit'],
                ['python3', EXE, 'config'],
                ['python3', EXE, 'configgg'],
                ['python3', EXE, 'config', 'restore'],
                ['python3', EXE, 'config', 'update'],
                ['python3', EXE, 'config', 'updateee']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        validate_output(expected=[["ERROR", ""]], output=output, cmd=cmd)


def test_config_restore_all():

    commands = [['python3', EXE, 'config', 'restore', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        assert "RESTORED" in output[0] and "all 29 settings to their defaults" in output[0], output


def test_config_show_all():

    commands = [['python3', EXE, 'config', 'show', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def validate_output(expected, output, cmd):

    for item in list(expected):
        for line in output:
            if item[0] in line and item[1] in line:
                if item in expected:
                    expected.remove(item)
    if expected:
        raise AssertionError("Not verified: {} for command: {}".format(expected, " ".join(cmd)))


def validate_results(passed, total, output, cmd):
    """
    Checks the summary's Total row and test count, or with -q the verdict line
    """
    quiet = "-q" in cmd
    output = _plain(output)
    if quiet:
        ok = any("{} passed".format(passed) in line for line in output)
    else:
        ok = any(line.split()[:2] == ["Total", str(passed)] for line in output if line.split()) and             any(line.strip().startswith("{} tests".format(total)) for line in output)
    if not ok:
        raise AssertionError("Not verified: {}/{} passed for command: {}".format(passed, total, " ".join(cmd)))


def test_run_with_cmd_args():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    for cmd in [['python3', EXE, 'run', '-s', TESTS, '-k', 'api'],
                ['python3', EXE, 'run', '-s', TESTS, '-k', 'api', '-q'],
                ['python3', EXE, 'run', '-s', TESTS, '-k', 'api', '--code-cov'],
                ['python3', EXE, 'run', '-s', TESTS, '-k', 'api', '--code-cov', '-q']]:
        output = Cmd.run(cmd)
        pprint.pprint(output)
        validate_results(6, 16, output, cmd)  # suites skipped by tags count as skipped


def test_run_with_config_and_cmd_args():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python3', EXE, 'config', 'update', '-k', 'api ui'])
    Cmd.run(['python3', EXE, 'config', 'update', '-g', 'sso'])
    cmd = ['python3', EXE, 'run', '-s', TESTS, '-k', 'api']
    output = Cmd.run(cmd)
    pprint.pprint(output)
    validate_results(4, 16, output, cmd)


def test_run_with_config():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python3', EXE, 'config', 'update', '-k', 'api', 'ui'])
    Cmd.run(['python3', EXE, 'config', 'update', '-g', 'sso'])
    cmd = ['python3', EXE, 'run', '-s', TESTS]
    output = Cmd.run(cmd)
    pprint.pprint(output)
    validate_results(9, 16, output, cmd)


def test_runner_with_config():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python3', EXE, 'config', 'update', '-k', 'ui'])
    Cmd.run(['python3', EXE, 'config', 'update', '-g', 'sso'])
    runner = Runner(suites=[ShoppingCartSuite, AuthApiSuite],
                    config=Config.get_config_path(CliConstants.TJ_CONFIG_NAME))
    runner.run()

    results = runner.get_executed_suites()
    tests_ShoppingCartSuite = results[0].get_test_objects()
    tests_AuthApiSuite = results[1].get_test_objects()
    pprint.pprint(results[0].metrics.get_metrics())

    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="success")
    print(len(tests_ShoppingCartSuite))
    assert len(tests_ShoppingCartSuite) == 5, \
        "Expected 5 tests to be executed, Actually executed: {}".format(len(tests_ShoppingCartSuite))
    assert len(tests_AuthApiSuite) == 6, \
        "Expected 6 tests to be executed, Actually executed: {}".format(len(tests_AuthApiSuite))
    for test in tests_ShoppingCartSuite:
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])
    for test in tests_AuthApiSuite:
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="skip",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"],
                                                  expected_retry_count=2,
                                                  expected_exception_count=2,
                                                  expected_performance_count=2)
                # should be 1 but there is a bug fix for which was reverted so will revisit once fixed


def test_runner_without_config():

    Cmd.run(['python3', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python3', EXE, 'config', 'update', '-k', 'ui'])
    Cmd.run(['python3', EXE, 'config', 'update', '-g', 'sso'])

    runner = Runner(suites=[NewProductsSuite])
    runner.run()
    results = runner.get_executed_suites()
    tests = results[0].get_test_objects()
    metrics = results[0].metrics.get_metrics()
    QualityManager.check_class_metrics(metrics, expected_status="success")

    assert len(tests) == 5, "Expected 5 tests to be executed, Actually executed: {}".format(len(tests))

    for test in tests:
        for class_param, class_data in test.metrics.get_metrics().items():
            for param, metrics in class_data.items():
                QualityManager.check_test_metrics(metrics,
                                                  expected_status="success",
                                                  expected_param=param,
                                                  expected_class_param=metrics["class_param"])
