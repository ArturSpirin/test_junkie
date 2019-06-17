import os
import pprint

from test_junkie.runner import Runner
from test_junkie.cli.config_manager import ConfigManager
from tests.QualityManager import QualityManager
from tests.cli.CliTestSuite import AuthApiSuite, ShoppingCartSuite, NewProductsSuite
from tests.cli.Cmd import Cmd

ROOT = __file__.split("{0}tests".format(os.sep))[0]
EXE = ROOT + "{0}test_junkie{0}cli{0}cli.py".format(os.sep)
TESTS = ROOT + "{0}tests{0}cli".format(os.sep)


def test_help():

    commands = [['python', EXE, '-h'],
                ['python', EXE, 'run', '-h'],
                ['python', EXE, 'scan', '-h'],
                ['python', EXE, 'config', '-h'],
                ['python', EXE, 'version', '-h']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception".format(cmd, output)


def test_sub_command_help():

    commands = [['python', EXE, 'scan', 'find', '-h'],
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
        for line in output:
            prop = cmd[4].replace("--", "")
            value = cmd[5] if len(cmd) == 6 else "True"
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "OK" in line
            assert prop in line, "Command: {} did not update property: {}".format(cmd, prop)
            assert value in line, "Command: {} did not update property: {} to value: {}".format(cmd, prop, value)


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


def test_config_restore_all():

    commands = [['python', EXE, 'config', 'restore', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)
            assert "Config restored to default settings!" in line, "Wrong message: {}".format(line)


def test_config_show_all():

    commands = [['python', EXE, 'config', 'show', '--all']]
    for cmd in commands:
        output = Cmd.run(cmd)
        for line in output:
            assert "Traceback (most recent call last)" not in line, \
                "Command: {} produced exception. {}".format(cmd, output)


def test_run_with_cmd_args():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    output = Cmd.run(['python', EXE, 'run', '-s', TESTS, '-k', 'api'])
    pprint.pprint(output)
    assert "[6/16 37.50%] SUCCESS" in output
    assert "[SUCCESS] [0/5 0%]" in output[-4] and "CliTestSuite.ShoppingCartSuite" in output[-4]
    assert "[SUCCESS] [0/5 0%]" in output[-3] and "CliTestSuite.NewProductsSuite" in output[-3]
    assert "[SUCCESS] [6/6 100.00%]" in output[-2] and "CliTestSuite.AuthApiSuite" in output[-2]


def test_run_with_config_and_cmd_args():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'api ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
    output = Cmd.run(['python', EXE, 'run', '-s', TESTS, '-k', 'api'])
    pprint.pprint(output)
    assert "[4/16 25.00%] SUCCESS" in output
    assert "[SUCCESS] [0/5 0%]" in output[-4] and "CliTestSuite.ShoppingCartSuite" in output[-4]
    assert "[SUCCESS] [0/5 0%]" in output[-3] and "CliTestSuite.NewProductsSuite" in output[-3]
    assert "[SUCCESS] [4/6 66.67%]" in output[-2] and "CliTestSuite.AuthApiSuite" in output[-2]


def test_run_with_config():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'api', 'ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
    output = Cmd.run(['python', EXE, 'run', '-s', TESTS])
    pprint.pprint(output)
    assert "[9/16 56.25%] SUCCESS" in output
    assert "[SUCCESS] [5/5 100.00%]" in output[-4] and "CliTestSuite.ShoppingCartSuite" in output[-4]
    assert "[SUCCESS] [0/5 0%]" in output[-3] and "CliTestSuite.NewProductsSuite" in output[-3]
    assert "[SUCCESS] [4/6 66.67%]" in output[-2] and "CliTestSuite.AuthApiSuite" in output[-2]


def test_runner_with_config():

    Cmd.run(['python', EXE, 'config', 'restore', '--all'])
    Cmd.run(['python', EXE, 'config', 'update', '-k', 'ui'])
    Cmd.run(['python', EXE, 'config', 'update', '-g', 'sso'])
    runner = Runner(suites=[ShoppingCartSuite, AuthApiSuite], config=ConfigManager().path)
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
