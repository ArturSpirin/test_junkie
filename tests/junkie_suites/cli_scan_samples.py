"""
Suite files in every style the CLI scanner has to recognise, plus helpers to write them to a temp dir and scan
it. Shared by the pytest and TJ test paths so both assert exactly the same thing.
"""
import os

from test_junkie.cli.cli_runner import CliRunner
from test_junkie.constants import Undefined

_BODY = """
    @test()
    def a_test(self):
        pass
"""

# file name -> (source, name of the suite it defines or None)
SAMPLES = {
    "a_plain.py": ("from test_junkie.decorators import Suite, test\n\n\n"
                   "@Suite()\nclass ScanPlain:\n" + _BODY, "ScanPlain"),
    "b_base_class.py": ("from test_junkie.decorators import Suite, test\n\n\nclass Base:\n    pass\n\n\n"
                        "@Suite()\nclass ScanWithBase(Base):\n" + _BODY, "ScanWithBase"),
    "c_trailing_comment.py": ("from test_junkie.decorators import Suite, test\n\n\n"
                              "@Suite()\nclass ScanWithComment:  # flaky area\n" + _BODY, "ScanWithComment"),
    "d_multiline_import.py": ("from test_junkie.decorators import (\n    Suite,\n    test,\n)\n\n\n"
                              "@Suite()\nclass ScanMultiLineImport:\n" + _BODY, "ScanMultiLineImport"),
    "e_multiline_decorator.py": ("from test_junkie.decorators import Suite, test\n\n\n"
                                 "@Suite(owner=\"qa\",\n       feature=\"Login\")\nclass ScanMultiLineDecorator:\n"
                                 + _BODY, "ScanMultiLineDecorator"),
    "f_module_alias.py": ("import test_junkie.decorators as tj\n\n\n"
                          "@tj.Suite()\nclass ScanModuleAlias:\n" + _BODY.replace("@test()", "@tj.test()"),
                          "ScanModuleAlias"),
    "g_import_alias.py": ("from test_junkie.decorators import Suite as S, test\n\n\n"
                          "@S()\nclass ScanImportAlias:\n" + _BODY, "ScanImportAlias"),
    # uses test_junkie but defines no suite - must not even be imported
    "h_not_a_suite.py": ("from test_junkie.runner import Runner\n\n"
                         "raise AssertionError('scanner imported a file that defines no suites')\n", None),
}

EXPECTED_SUITES = [name for _, (_, name) in sorted(SAMPLES.items()) if name]


def write_samples(directory):
    for file_name, (source, _) in SAMPLES.items():
        with open(os.path.join(directory, file_name), "w") as doc:
            doc.write(source)


def scan(*sources):
    """
    :return: LIST of suite class names found by the CLI scanner, in discovery order
    """
    runner = CliRunner(sources=[str(source) for source in sources], ignore=[".git"], suites=None,
                       code_cov=False, cov_rcfile=None, guess_root=False, config=Undefined)
    runner.scan()
    return [suite.__name__ for suite in runner.suites]
