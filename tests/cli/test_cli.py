import os
import pprint

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

    commands = [['python', EXE, '-h'],
                ['python', EXE, 'run', '-h'],
                ['python', EXE, 'audit', '-h'],
                ['python', EXE, 'config', '-h'],
                ['python', EXE, 'version', '-h']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception".format(cmd, output)


def test_sub_command_help():

    commands = [['python', EXE, 'audit', 'find', '-h'],
                ['python', EXE, 'config', 'update', '-h'],
                ['python', EXE, 'config', 'show', '-h'],
                ['python', EXE, 'config', 'restore', '-h']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def test_incomplete_inputs():

    commands = [
                ['python', EXE, 'config'],
                ['python', EXE, 'config', 'update'],
                ['python', EXE, 'config', 'restore'],
                ['python', EXE, 'config', 'show'],
                ['python', EXE, 'version']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def test_config_update():

    commands = [['python', EXE, 'config', 'update', '--test_multithreading_limit', '10'],
                ['python', EXE, 'config', 'update', '--suite_multithreading_limit', '10'],
                ['python', EXE, 'config', 'update', '--features', 'feat'],
                ['python', EXE, 'config', 'update', '--components', 'comp'],
                ['python', EXE, 'config', 'update', '--owners', 'own'],
                ['python', EXE, 'config', 'update', '--monitor_resources'],
                ['python', EXE, 'config', 'update', '--html_report', '/test/path/for/html'],
                ['python', EXE, 'config', 'update', '--xml_report', '/test/path/for/xml'],
                ['python', EXE, 'config', 'update', '--run_on_match_all', '1000'],
                ['python', EXE, 'config', 'update', '--run_on_match_any', '2000'],
                ['python', EXE, 'config', 'update', '--skip_on_match_all', '3000'],
                ['python', EXE, 'config', 'update', '--skip_on_match_any', '4000'],
                ]
    for cmd in commands:
        output = Cmd.run(cmd)

        prop = cmd[4].replace("--", "")
        value = cmd[5] if len(cmd) == 6 else "True"
        assert "Traceback (most recent call last)" not in output[-2], \
            "Command: {} produced exception. {}".format(cmd, output)
        assert "OK" in output[-2]
        assert prop in output[-2], "Command: {} did not update property: {}".format(cmd, prop)
        assert value in output[-2], "Command: {} did not update property: {} to value: {}".format(cmd, prop, value)


def test_config_restore():

    commands = [['python', EXE, 'config', 'restore', '--test_multithreading_limit'],
                ['python', EXE, 'config', 'restore', '--suite_multithreading_limit'],
                ['python', EXE, 'config', 'restore', '--features'],
                ['python', EXE, 'config', 'restore', '--components'],
                ['python', EXE, 'config', 'restore', '--owners'],
                ['python', EXE, 'config', 'restore', '--monitor_resources'],
                ['python', EXE, 'config', 'restore', '--html_report'],
                ['python', EXE, 'config', 'restore', '--xml_report'],
                ['python', EXE, 'config', 'restore', '--run_on_match_all'],
                ['python', EXE, 'config', 'restore', '--run_on_match_any'],
                ['python', EXE, 'config', 'restore', '--skip_on_match_all'],
                ['python', EXE, 'config', 'restore', '--skip_on_match_any'],
                ]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            prop = cmd[4].replace("--", "")
            value = "None"
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "OK" in line
            assert prop in line, "Command: {} did not update property: {}".format(cmd, prop)
            assert value in line, "Command: {} did not update property: {} to value: {}".format(cmd, prop, value)


def test_audit_all():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS],
                ['python', EXE, 'audit', '-s', TESTS, '--by-suites', '--by-tags',
                 '--by-owners', '--by-features', '--by-components', '--by-suites']]
    for cmd in commands:
        output = Cmd.run(cmd)
        not_validated = ["FEATURES", "OWNERS", "SUITES", "COMPONENTS", "TAGS"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_audit_by_owner():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS, '--by-owners'],
                ['python', EXE, 'audit', '-s', TESTS, '--by-owners', '-o', 'Mike']]
    for cmd in commands:
        output = Cmd.run(cmd)
        assert_not_in = ["FEATURES", "SUITES", "COMPONENTS", "TAGS"]
        if "Mike" in cmd:
            assert_not_in.append("Victor")
            assert_not_in.append("George")
            assert_not_in.append("None")
            assert_not_in.append("Owners:")
        not_validated = ["OWNERS", "Mike", "Suites:", "Features:", "Components:", "Tags:"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for item in assert_not_in:
                assert item not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_audit_by_suite():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS, '--by-suites'],
                ['python', EXE, 'audit', '-s', TESTS, '--by-suites', '-o', 'Mike']]
    for cmd in commands:
        output = Cmd.run(cmd)
        assert_not_in = ["FEATURES", "OWNERS", "COMPONENTS", "TAGS"]
        if "Mike" in cmd:
            assert_not_in.append("Victor")
            assert_not_in.append("George")
            assert_not_in.append("None")
            assert_not_in.append("Suites:")
        not_validated = ["SUITES", "Mike", "Owners:", "Feature:", "Components:", "Tags:"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for item in assert_not_in:
                assert item not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_audit_by_tags():
    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS, '--by-tags'],
                ['python', EXE, 'audit', '-s', TESTS, '--by-tags', '-l', 'sso']]
    for cmd in commands:
        output = Cmd.run(cmd)
        assert_not_in = ["FEATURES", "OWNERS", "COMPONENTS", "SUITES"]
        if "Mike" in cmd:
            assert_not_in.append("Victor")
            assert_not_in.append("George")
            assert_not_in.append("None")
            assert_not_in.append("Tags:")
        not_validated = ["TAGS", "Mike", "Owners:", "Features:", "Suites:", "Components:", "API(2)"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for item in assert_not_in:
                assert item not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_audit_by_features():
    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS, '--by-features'],
                ['python', EXE, 'audit', '-s', TESTS, '--by-features', '-f', 'Store']]
    for cmd in commands:
        output = Cmd.run(cmd)
        assert_not_in = ["SUITES", "OWNERS", "COMPONENTS", "SUITES", "TAGS"]
        if "Mike" in cmd:
            assert_not_in.append("Mike")
            assert_not_in.append("None")
            assert_not_in.append("Features:")
        not_validated = ["FEATURES", "Mike(5)", "George(5)", "Owners:", "Tags:", "Suites:", "Components:"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for item in assert_not_in:
                assert item not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_audit_by_components():
    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    commands = [['python', EXE, 'audit', '-s', TESTS, '--by-components'],
                ['python', EXE, 'audit', '-s', TESTS, '--by-components', '-c', 'Admin']]
    for cmd in commands:
        output = Cmd.run(cmd)
        assert_not_in = ["SUITES", "OWNERS", "FEATURES", "SUITES", "TAGS"]
        if "Mike" in cmd:
            assert_not_in.append("George")
            assert_not_in.append("None")
            assert_not_in.append("Features:")
        not_validated = ["COMPONENTS", "Mike(5)", "Owners:", "Tags:", "Suites:", "Features:"]
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "ERROR" not in line
            for item in assert_not_in:
                assert item not in line
            for validate in list(not_validated):
                if validate in line:
                    not_validated.remove(validate)
        assert len(not_validated) == 0


def test_bad_inputs():

    commands = [['python', EXE, 'run'],
                ['python', EXE, 'audit'],
                ['python', EXE, 'config'],
                ['python', EXE, 'configgg'],
                ['python', EXE, 'config', 'restore'],
                ['python', EXE, 'config', 'update'],
                ['python', EXE, 'config', 'updateee']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        validate_output(expected=[["[ERROR]", ""]], output=output)


def test_config_restore_all():

    commands = [['python', EXE, 'config', 'restore', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
        assert "Config restored to default settings!" in output[-1], "Wrong message: {}".format(output[-1])


def test_config_show_all():

    commands = [['python', EXE, 'config', 'show', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def validate_output(expected, output):

    for item in list(expected):
        for line in output:
            if item[0] in line and item[1] in line:
                expected.remove(item)
    if expected:
        raise AssertionError("Not verified: {}".format(expected))


def test_run_with_cmd_args():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    for cmd in [['python', EXE, 'run', '-s', TESTS, '-k', 'api'],
                ['python', EXE, 'run', '-s', TESTS, '-k', 'api', '-q'],
                ['python', EXE, 'run', '-s', TESTS, '-k', 'api', '--code-cov'],
                ['python', EXE, 'run', '-s', TESTS, '-k', 'api', '--code-cov', '-q']]:
        output = Cmd.run(cmd)
        pprint.pprint(output)
        validate_output(expected=[["[6/16 37.50%]", "SUCCESS"],
                                  ["[SUCCESS] [0/5 0%]", "CliTestSuite.ShoppingCartSuite"],
                                  ["[SUCCESS] [0/5 0%]", "CliTestSuite.NewProductsSuite"],
                                  ["[SUCCESS] [6/6 100.00%]", "CliTestSuite.AuthApiSuite"]],
                        output=output)
        if "--code-cov" in cmd:
            validate_output(expected=[["Coverage reports can be accessed via coverage cli",
                                       "Try \"coverage report -m\". For more see \"coverage -h\""]],
                            output=output)


def test_run_with_config_and_cmd_args():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'api ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
    output = Cmd.run(['python', EXE, 'run', '-s', TESTS, '-k', 'api'])
    pprint.pprint(output)
    validate_output(expected=[["[4/16 25.00%]", "SUCCESS"],
                              ["[SUCCESS] [0/5 0%]", "CliTestSuite.ShoppingCartSuite"],
                              ["[SUCCESS] [0/5 0%]", "CliTestSuite.NewProductsSuite"],
                              ["[SUCCESS] [4/6 66.67%]", "CliTestSuite.AuthApiSuite"]],
                    output=output)


def test_run_with_config():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'api', 'ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
    output = Cmd.run(['python', EXE, 'run', '-s', TESTS])
    pprint.pprint(output)
    validate_output(expected=[["[9/16 56.25%]", "SUCCESS"],
                              ["[SUCCESS] [5/5 100.00%]", "CliTestSuite.ShoppingCartSuite"],
                              ["[SUCCESS] [0/5 0%]", "CliTestSuite.NewProductsSuite"],
                              ["[SUCCESS] [4/6 66.67%]", "CliTestSuite.AuthApiSuite"]],
                    output=output)


def test_runner_with_config():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
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

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])

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
