"""
In-process CLI checks (tj run / audit / config / version) shared by the pytest and TJ test paths. Each check
runs the real CLI entry point with a patched sys.argv, captures stdout and the exit code, and always points
TEST_JUNKIE_HOME at a throwaway dir so the developer's real config is never touched.
"""
import contextlib
import io
import os
import re
import shutil
import sys
import tempfile

from test_junkie.constants import CliConstants

_ANSI = re.compile(r"\x1b\[[0-9;]*m")

AUDIT_SUITES = '''
from test_junkie.decorators import Suite, test
from test_junkie.listener import Listener
from test_junkie.rules import Rules


class AuditRules(Rules):
    pass


class AuditListener(Listener):
    pass


@Suite(feature="Billing", owner="alice", retry=2, meta={"area": "billing"}, rules=AuditRules,
       listener=AuditListener)
class AuditFull:

    @test(component="pay", tags=["smoke"], owner="bob", retry=2, meta={"ticket": "B-1"}, parameters=[1, 2])
    def charge(self, parameter):
        pass


@Suite(meta={"area": "suite-only"})
class AuditSuiteMetaOnly:

    @test()
    def no_meta(self):
        pass


@Suite()
class AuditBare:

    @test()
    def plain(self):
        pass
'''

PASSING_SUITE = '''
from test_junkie.decorators import Suite, test


@Suite()
class CliPassingSuite:

    @test()
    def passes(self):
        pass
'''

FAILING_SUITE = '''
from test_junkie.decorators import Suite, test


@Suite()
class CliFailingSuite:

    @test()
    def fails(self):
        assert False
'''


COVERAGE_RC = """[run]
branch = True
"""

BROKEN_CONFIG = """not a config file
"""

INTERRUPTED_IMPORT = """raise KeyboardInterrupt
""" + PASSING_SUITE

INTERRUPTED_TEST = PASSING_SUITE.replace("""    def passes(self):
        pass""", """    def passes(self):
        raise KeyboardInterrupt""")

BROKEN_LISTENER = """from test_junkie.listener import Listener


class Broken(Listener):

    def on_success(self, **kwargs):
        raise ValueError("listener bug")
""" + PASSING_SUITE.replace("@Suite()", "@Suite(listener=Broken)")

UNRESOLVABLE_IMPORT = """import module_that_does_not_exist_tj
""" + PASSING_SUITE


def run_cli(*argv, home=None, cwd=None, home_files=None, keep_home=False):
    """
    :param home: TEST_JUNKIE_HOME to use - defaults to a fresh temp dir (may point at a dir that doesn't exist yet)
    :param cwd: run with this working directory
    :param home_files: DICT of file name -> contents to put in the home dir first (e.g. a broken config)
    :return: (exit code - None if the command returned normally, stdout with colors stripped)
    """
    from test_junkie.cli.cli import Cli
    home = home or tempfile.mkdtemp()
    for name, contents in (home_files or {}).items():
        os.makedirs(home, exist_ok=True)
        with open(os.path.join(home, name), "w") as doc:
            doc.write(contents)
    previous_home, previous_argv, previous_cwd = os.environ.get(CliConstants.HOME_ENV_VAR), sys.argv, os.getcwd()
    os.environ[CliConstants.HOME_ENV_VAR] = home
    sys.argv = ["tj"] + [str(arg) for arg in argv]
    out = io.StringIO()
    code = None
    try:
        if cwd:
            os.chdir(cwd)
        with contextlib.redirect_stdout(out):
            Cli()
    except SystemExit as exit_:
        code = exit_.code
    finally:
        os.chdir(previous_cwd)
        sys.argv = previous_argv
        if previous_home is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous_home
        if not keep_home:
            shutil.rmtree(home, ignore_errors=True)
    return code, _ANSI.sub("", out.getvalue())


def _write(source, name):
    directory = tempfile.mkdtemp()
    with open(os.path.join(directory, name), "w") as doc:
        doc.write(source)
    return directory


def _audited_suites(*flags):
    code, out = run_cli("audit", "suites", "-s", _write(AUDIT_SUITES, "audit_suites.py"), *flags)
    assert code is None, out
    return sorted(set(re.findall(r"^(Audit\w+) +\d+ tests?", out, re.M)))  # block titles


def audit_lists_every_suite():
    assert _audited_suites() == ["AuditBare", "AuditFull", "AuditSuiteMetaOnly"]


def audit_no_flags_filter_out_suites_that_have_them():
    for flag in ("--no-rules", "--no-listeners", "--no-suite-retries", "--no-owners", "--no-features",
                 "--no-test-retries", "--no-components", "--no-tags"):
        assert "AuditFull" not in _audited_suites(flag), flag
    assert _audited_suites("--no-suite-meta") == ["AuditBare"]


def audit_no_test_meta_checks_the_tests_meta():
    # used to check the *suite's* meta, so a suite with meta but plain tests was wrongly filtered out
    assert _audited_suites("--no-test-meta") == ["AuditBare", "AuditSuiteMetaOnly"]


def audit_only_covers_the_requested_suites():
    # used to walk every suite registered in the process, so -x was ignored
    assert _audited_suites("-x", "AuditBare") == ["AuditBare"]


def audit_by_feature_and_verbose():
    code, out = run_cli("audit", "features", "-v", "-s", _write(AUDIT_SUITES, "audit_suites.py"))
    assert code is None and re.search(r"^Billing +1 test ", out, re.M), out
    assert re.search(r"^no feature +2 tests", out, re.M), out  # the suites without a feature get their own block


def audit_unknown_view_is_rejected():
    code, out = run_cli("audit", "nonsense", "-s", _write(AUDIT_SUITES, "audit_suites.py"))
    assert code == 120 and "'nonsense' is not an audit view" in out, out
    code, out = run_cli("audit")
    assert code == 120 and "Which view?" in out, out


def audit_and_run_without_sources_explain_what_is_missing():
    for command in (["audit", "suites"], ["run"]):
        code, out = run_cli(*command)
        assert code == 120 and "Sources is a required parameter" in out, (command, out)


def audit_reports_when_nothing_matches():
    code, out = run_cli("audit", "suites", "-s", _write(AUDIT_SUITES, "audit_suites.py"), "--features", "Nope")
    assert code is None and "Nothing matches. 3 tests were scanned, none of them matches: features Nope" in out, out


def run_exit_codes():
    code, out = run_cli("run", "-s", _write(PASSING_SUITE, "passing_suite.py"), "-v")
    assert code is None, out  # returns normally = exit 0
    code, out = run_cli("run", "-s", _write(FAILING_SUITE, "failing_suite.py"))
    assert code == 1, out
    code, out = run_cli("run", "-s", tempfile.mkdtemp())  # no suites
    assert code == 1, out


def run_with_missing_config_file():
    code, out = run_cli("run", "-s", _write(PASSING_SUITE, "passing_suite.py"), "--config", "no_such_config.cfg")
    assert code == 120 and "Wasn't able to find config" in out, out


def run_import_error_and_guess_root():
    project = tempfile.mkdtemp()
    os.makedirs(os.path.join(project, "proj_helpers_tj"))
    with open(os.path.join(project, "proj_helpers_tj", "__init__.py"), "w") as doc:
        doc.write("VALUE = 1\n")
    os.makedirs(os.path.join(project, "suites"))
    with open(os.path.join(project, "suites", "needs_root.py"), "w") as doc:
        doc.write("from proj_helpers_tj import VALUE\n" + PASSING_SUITE.replace("CliPassingSuite", "NeedsRootSuite"))
    # the project root isn't importable from the suite file on its own
    code, out = run_cli("run", "-s", os.path.join(project, "suites"))
    assert code == 120 and "There is an import error" in out, out
    # --guess-root walks up from the file until the import resolves
    code, out = run_cli("run", "-s", os.path.join(project, "suites"), "--guess-root")
    assert code is None and "Trying again with assumption that this is your project root" in out, out
    sys.modules.pop("proj_helpers_tj", None)


def guess_root_with_a_relative_source():
    # with a relative -s (tj run -s suites --guess-root) the first guess was "suites" itself, and walking up from a
    # relative path stopped there - so it gave up instead of trying the project root above it
    project = tempfile.mkdtemp()
    os.makedirs(os.path.join(project, "proj_rel_helpers_tj"))
    with open(os.path.join(project, "proj_rel_helpers_tj", "__init__.py"), "w") as doc:
        doc.write("VALUE = 1\n")
    os.makedirs(os.path.join(project, "suites"))
    with open(os.path.join(project, "suites", "needs_rel_root.py"), "w") as doc:
        doc.write("from proj_rel_helpers_tj import VALUE\n" +
                  PASSING_SUITE.replace("CliPassingSuite", "NeedsRelRootSuite"))
    saved = list(sys.path)
    # python -m pytest / python -m test_junkie put the working directory on sys.path, which would hide the bug
    sys.path[:] = [entry for entry in sys.path if entry not in ("", ".")]
    try:
        code, out = run_cli("run", "-s", "suites", cwd=project)
        assert code == 120 and "There is an import error" in out, out
        code, out = run_cli("run", "-s", "suites", "--guess-root", cwd=project)
        assert code is None and "1 suite, 1 test" in out and "PASSED" in out, out
    finally:
        sys.path[:] = saved
        sys.modules.pop("proj_rel_helpers_tj", None)


def config_commands():
    for command, text in ((("config", "update"), "Nothing to update"), (("config", "restore"), "Nothing to restore"),
                          (("config", "show"), "Which settings?"), (("config",), "Which config command?"),
                          (("config", "nonsense"), "'nonsense' is not a config command"),
                          (("config", "update", "-T", "four"), 'needs a whole number, got "four"')):
        code, out = run_cli(*command)
        assert code == 120 and "[ERROR]" in out and text in out, (command, out)
    code, out = run_cli("config", "show", "--all")
    assert code is None and "Config  " in out and "Discovery" in out and "0 of 20 settings saved" in out, out
    code, out = run_cli("config", "show", "--sources")
    assert code is None and re.search(r"^  sources +\.$", out, re.M), out  # unset: a dot (ASCII for ·)


def config_update_show_restore():
    home = tempfile.mkdtemp()
    code, out = run_cli("config", "update", "-s", "tests", "-T", "4", home=home, keep_home=True)
    assert code is None and "[SAVED]  2 settings" in out, out
    assert re.search(r"^  test_multithreading_limit +\. +-> +4$", out, re.M), out  # was unset
    assert "Undo: tj config restore -T -s" in out or "Undo: tj config restore -s -T" in out, out
    code, out = run_cli("config", "update", "-T", "2", home=home, keep_home=True)
    assert re.search(r"^  test_multithreading_limit +4 +-> +2$", out, re.M), out
    code, out = run_cli("config", "show", "--all", home=home, keep_home=True)
    assert "2 of 20 settings saved" in out and re.search(r"^  sources +tests$", out, re.M), out
    code, out = run_cli("config", "restore", "-T", home=home, keep_home=True)
    assert "[RESTORED]  1 setting to its default" in out and re.search(
        r"^  test_multithreading_limit +2 +-> +default 1$", out, re.M), out
    code, out = run_cli("config", "restore", "--all", home=home, keep_home=True)
    assert "all 20 settings to their defaults . 1 had values" in out and "sources" in out, out
    # tj config update --no-capture is read back by tj run
    code, out = run_cli("config", "update", "--no-capture", home=home, keep_home=True)
    from test_junkie.settings import Settings
    previous = os.environ.get(CliConstants.HOME_ENV_VAR)
    os.environ[CliConstants.HOME_ENV_VAR] = home
    try:
        assert Settings({"config": CliConstants.TJ_CONFIG_NAME}, {}).capture is False
    finally:
        if previous is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous
        shutil.rmtree(home, ignore_errors=True)


def run_shows_the_saved_config_it_used():
    home = tempfile.mkdtemp()
    directory = _write(PASSING_SUITE, "passing_suite.py")
    run_cli("config", "update", "-T", "2", "-k", "nothing_has_this_tag", home=home, keep_home=True)
    code, out = run_cli("run", "-s", directory, home=home, keep_home=True)
    lines = out.splitlines()
    config = [index for index, line in enumerate(lines) if line.startswith("  config   ")]
    assert config and home in lines[config[0]], out
    assert "run_on_match_any nothing_has_this_tag" in lines[config[0] + 1] and \
        "test_multithreading_limit 2" in lines[config[0] + 1], out
    # a setting passed on the command line wins, so it isn't listed as coming from the config
    code, out = run_cli("run", "-s", directory, "-T", "1", "-k", "x", home=home)
    assert "  config   " not in out, out
    code, out = run_cli("run", "-s", directory)  # nothing saved: no config row
    assert "  config   " not in out, out


def audit_views_gaps_and_listing():
    directory = _write(AUDIT_SUITES, "audit_suites.py")
    code, out = run_cli("audit", "owners", "-s", directory)
    assert code is None and re.search(r"^bob +1 test . +33%", out, re.M), out
    assert re.search(r"^no owner +2 tests", out, re.M), out  # untested-by-anyone gets its own block, last
    assert "Gaps 4" in out and "tj audit owners --no-owners" in out, out
    assert "3 tests . 3 suites . 1 feature . 1 owner . 1 component . 1 tag" in out, out
    code, out = run_cli("audit", "suites", "-s", directory, "--no-owners")
    assert "filters  no owner" in out and re.search(r"^  tests +plain$", out, re.M), out  # filters list the tests
    code, out = run_cli("audit", "components", "-s", directory, "--by-features")
    assert re.search(r"^  feature +Billing 1$", out, re.M) and "audit    components . by features" in out, out


def unknown_command_and_version():
    code, out = run_cli("nonsense")
    assert code == 1 and "is not a test-junkie command" in out, out
    code, out = run_cli("version")
    assert code is None and out.startswith("Test Junkie "), out


def run_with_code_coverage():
    # own working dir, so the inner coverage session doesn't pick up the repo's .coveragerc or write data files into it
    directory = _write(PASSING_SUITE, "passing_suite.py")
    code, out = run_cli("run", "-s", directory, "--code-cov", cwd=directory)
    assert code is None and "Code coverage report:" in out, out
    rcfile = os.path.join(directory, "cov.rc")
    with open(rcfile, "w") as doc:
        doc.write(COVERAGE_RC)
    code, out = run_cli("run", "-s", directory, "--code-cov", "--cov-rcfile", rcfile, cwd=directory)
    assert code is None and "Code coverage report:" in out, out


def ctrl_c_exits_12():
    code, out = run_cli("run", "-s", _write(INTERRUPTED_IMPORT, "interrupted_scan.py"))
    assert code == 12 and "(Ctrl+C) Exiting!" in out, out
    # a KeyboardInterrupt in a test cancels the run like Ctrl+C: summary and reports are still written
    code, out = run_cli("run", "-s", _write(INTERRUPTED_TEST, "interrupted_run.py"))
    assert code == 12 and "CANCELLED" in out and "exit code 12" in out and "Summary" in out, out


def unexpected_error_during_run_exits_120():
    code, out = run_cli("run", "-s", _write(BROKEN_LISTENER, "broken_listener.py"))
    assert code == 120 and "Unexpected error during test execution" in out, out


def guess_root_gives_up_when_nothing_resolves():
    code, out = run_cli("run", "-s", _write(UNRESOLVABLE_IMPORT, "unresolvable.py"), "--guess-root")
    assert code == 120 and "There is an import error" in out, out


def git_folders_are_not_scanned():
    directory = _write(PASSING_SUITE, "passing_suite.py")
    os.makedirs(os.path.join(directory, ".git", "hooks"))
    with open(os.path.join(directory, ".git", "hooks", "hidden_suite.py"), "w") as doc:
        doc.write(PASSING_SUITE.replace("CliPassingSuite", "HiddenInGitSuite"))
    code, out = run_cli("run", "-s", directory)
    assert code is None and "1 suite, 1 test" in out and "HiddenInGitSuite" not in out, out



def same_named_files_and_stdlib_names():
    # every suite file used to be loaded under its bare file name: tests/a/login.py and tests/b/login.py were both
    # `login` (audit merged their suites), and a suite file named json.py replaced the real json module - the HTML
    # report then crashed with "module 'json' has no attribute 'dumps'"
    import json
    directory = tempfile.mkdtemp()
    for folder, test_name in (("a", "from_a"), ("b", "from_b")):
        os.makedirs(os.path.join(directory, folder))
        with open(os.path.join(directory, folder, "login.py"), "w") as doc:
            doc.write(PASSING_SUITE.replace("CliPassingSuite", "SameNameSuite").replace("def passes", "def " + test_name))
    with open(os.path.join(directory, "b", "json.py"), "w") as doc:
        doc.write(PASSING_SUITE.replace("CliPassingSuite", "StdlibNamedSuite"))
    with open(os.path.join(directory, "json.py"), "w") as doc:  # bare and dotted name both taken
        doc.write(PASSING_SUITE.replace("CliPassingSuite", "RootStdlibNamedSuite"))
    report = os.path.join(directory, "report.html")
    code, out = run_cli("run", "-s", directory, "--html_report", report, cwd=directory)
    assert code is None and "4 suites, 4 tests" in out, out
    assert sys.modules["json"] is json and hasattr(json, "dumps")
    with io.open(report, encoding="utf-8") as doc:
        html = doc.read()
    assert "from_a" in html and "from_b" in html
    code, out = run_cli("audit", "suites", "-s", directory, cwd=directory)
    audited = re.findall(r"^(\S*SameNameSuite) +\d+ test", out, re.M)
    assert code is None and len(set(audited)) == 2, out  # listed separately, as module.SameNameSuite
    shutil.rmtree(directory, ignore_errors=True)


def audit_no_owners_checks_test_owners():
    source = PASSING_SUITE.replace("CliPassingSuite", "AuditTestOwner").replace("@test()", "@test(owner=\"carol\")")
    directory = _write(source, "test_owner.py")
    code, out = run_cli("audit", "suites", "-s", directory)
    assert code is None and "AuditTestOwner" in out, out
    code, out = run_cli("audit", "suites", "-s", directory, "--no-owners")
    assert "AuditTestOwner" not in out, out


def code_coverage_report_failure_exits_120():
    # nothing measured -> coverage can't report ("No data to report")
    directory = _write(PASSING_SUITE, "passing_suite.py")
    rcfile = os.path.join(directory, "cov.rc")
    with open(rcfile, "w") as doc:
        doc.write("[run]\nsource = no_such_package_tj\n")
    code, out = run_cli("run", "-s", directory, "--code-cov", "--cov-rcfile", rcfile, cwd=directory)
    assert code == 120, out


def config_update_that_cannot_be_saved_exits_120():
    import stat
    home = tempfile.mkdtemp()
    config = os.path.join(home, CliConstants.TJ_CONFIG_NAME)
    with open(config, "w") as doc:
        doc.write("[runtime]\n")
    os.chmod(config, stat.S_IREAD)
    try:
        code, out = run_cli("config", "update", "--sources", home, home=home)
        assert code == 120 and "Unexpected error occurred during update" in out, out
    finally:
        if os.path.exists(config):  # run_cli already removed it on Linux; Windows can't delete a read-only file
            os.chmod(config, stat.S_IREAD | stat.S_IWRITE)
        shutil.rmtree(home, ignore_errors=True)


def config_dir_is_created_on_first_use():
    home = os.path.join(tempfile.mkdtemp(), "not", "created", "yet")
    code, out = run_cli("config", "show", "--all", home=home)
    assert code is None and "Config  " in out and "Discovery" in out, out


def config_values_with_percent_signs():
    # "%" used to be treated as configparser interpolation - saving a report path like this failed
    home = tempfile.mkdtemp()
    code, out = run_cli("config", "update", "--html_report", "reports/100%/r.html", home=home)
    assert code is None and re.search(r"^  html_report +\. +-> +reports/100%/r.html$", out, re.M), out


def broken_config_fails_cleanly():
    broken = {CliConstants.TJ_CONFIG_NAME: BROKEN_CONFIG}
    for command in (["config", "show", "--sources"], ["config", "update", "--owners", "qa"]):
        # used to exit 0 after the error was printed
        code, out = run_cli(*command, home_files=broken)
        assert code == 120 and ("Error" in out or "error" in out), (command, out)


def config_helpers():
    from test_junkie.cli.cli import CliUtils
    from test_junkie.cli.cli_config import Config
    assert Config.parse(5) == 5 and Config.parse("['a']") == ["a"] and Config.parse("report.html") == "report.html"
    home = tempfile.mkdtemp()
    previous = os.environ.get(CliConstants.HOME_ENV_VAR)
    os.environ[CliConstants.HOME_ENV_VAR] = home
    try:
        assert "[runtime]" in Config(CliConstants.TJ_CONFIG_NAME).read()
    finally:
        if previous is None:
            del os.environ[CliConstants.HOME_ENV_VAR]
        else:
            os.environ[CliConstants.HOME_ENV_VAR] = previous
        shutil.rmtree(home, ignore_errors=True)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        CliUtils.print_color_traceback(trace="custom trace text")
    assert "custom trace text" in out.getvalue()


CHECKS = [audit_lists_every_suite, guess_root_with_a_relative_source, config_update_show_restore, run_shows_the_saved_config_it_used, audit_views_gaps_and_listing, audit_no_flags_filter_out_suites_that_have_them,
          audit_no_test_meta_checks_the_tests_meta, audit_only_covers_the_requested_suites, audit_by_feature_and_verbose, audit_unknown_view_is_rejected,
          audit_and_run_without_sources_explain_what_is_missing, audit_reports_when_nothing_matches,
          run_exit_codes, run_with_missing_config_file, run_import_error_and_guess_root, config_commands,
          unknown_command_and_version, run_with_code_coverage, ctrl_c_exits_12,
          unexpected_error_during_run_exits_120, guess_root_gives_up_when_nothing_resolves,
          git_folders_are_not_scanned, same_named_files_and_stdlib_names, audit_no_owners_checks_test_owners,
          code_coverage_report_failure_exits_120, config_update_that_cannot_be_saved_exits_120,
          config_dir_is_created_on_first_use, config_values_with_percent_signs,
          broken_config_fails_cleanly, config_helpers]
