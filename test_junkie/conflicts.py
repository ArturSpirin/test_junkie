"""
conflicts_with= (formerly pr=): which tests must never run at the same time.

Targets can be a @test function, a @Suite class (all of its tests), or their names as text ("Suite", "Suite.test").
They're declared on @test() or @Suite() (every test of the suite). Everything is resolved and checked once, when a
run starts, into a symmetric map between tests: if A conflicts with B, B conflicts with A.
"""
import inspect
import warnings

from test_junkie.constants import DocumentationLinks
from test_junkie.errors import BadParameters


def _name(test):
    return "{}.{}".format(test.suite.get_class_name(), test.get_function_name())


class ConflictMap(object):

    def __init__(self, tests_by_key=None, conflicts=None, suite_conflicts=None):
        self.__tests = tests_by_key or {}  # function object -> TestObject
        self.__conflicts = conflicts or {}  # function object -> set(function objects)
        self.__suite_conflicts = suite_conflicts or {}  # suite class -> set(suite classes)

    def conflicts(self, test):
        """function objects of the tests that must not run while `test` runs"""
        return self.__conflicts.get(test.get_function_object(), set())

    def suite_conflicts(self, suite):
        """suite classes whose suite thread must not run alongside `suite` (suite-to-suite declarations)"""
        return self.__suite_conflicts.get(suite.get_class_object(), set())

    def name(self, key):
        test = self.__tests.get(key)
        return _name(test) if test is not None else getattr(key, "__qualname__", str(key))

    def pairs(self):
        """[(name, name)] of every declared conflict, each pair once, sorted - for tj audit"""
        seen = set()
        for key, others in self.__conflicts.items():
            for other in others:
                seen.add(tuple(sorted((self.name(key), self.name(other)))))
        return sorted(seen)

    @staticmethod
    def build(suite_objects, known_suite_objects):
        """
        :param suite_objects: the SuiteObjects in this run, whose declarations are checked
        :param known_suite_objects: every SuiteObject Test Junkie knows, so a target outside this run isn't an error
        :raises BadParameters: for a target of the wrong type, a name that matches nothing, or a self-reference
        """
        by_class = {suite.get_class_object(): suite for suite in known_suite_objects}
        by_name = {}
        for suite in known_suite_objects:
            by_name.setdefault(suite.get_class_name(), []).append(suite)
        tests = {test.get_function_object(): test for suite in known_suite_objects for test in suite.get_test_objects()}
        old_name = []

        def resolve(target, owner, owner_is_test):
            """:return: (set of test function objects, suite class or None)"""
            kind = "test" if owner_is_test else "suite"
            if isinstance(target, str):
                suite_name, _, test_name = target.partition(".")
                matches = by_name.get(suite_name, [])
                if len(matches) > 1:
                    raise BadParameters("conflicts_with on {} {}: more than one suite is called {!r}; pass the class "
                                        "instead. See documentation: {}".format(kind, owner, suite_name,
                                                                                DocumentationLinks.THREADING))
                if not matches:
                    raise BadParameters(_unknown(kind, owner, target, owner_is_test))
                suite = matches[0]
                if not test_name:
                    return {t.get_function_object() for t in suite.get_test_objects()}, suite.get_class_object()
                found = [t for t in suite.get_test_objects() if t.get_function_name() == test_name]
                if not found:
                    raise BadParameters(_unknown(kind, owner, target, owner_is_test))
                return {found[0].get_function_object()}, None
            if inspect.isclass(target):
                suite = by_class.get(target)
                if suite is None:
                    raise BadParameters(_unknown(kind, owner, target, owner_is_test))
                return {t.get_function_object() for t in suite.get_test_objects()}, target
            if inspect.isfunction(target) or inspect.ismethod(target):
                function = getattr(target, "__func__", target)
                if function not in tests:
                    raise BadParameters(_unknown(kind, owner, target, owner_is_test))
                return {function}, None
            raise BadParameters(_unknown(kind, owner, target, owner_is_test))

        forward = {}
        suite_forward = {}
        for suite in suite_objects:
            if "pr" in suite.get_kwargs():
                old_name.append(suite.get_class_name())
            suite_targets = set()
            for target in suite.get_parallel_restrictions():
                keys, target_suite = resolve(target, suite.get_class_name(), False)
                if target_suite is suite.get_class_object():
                    raise BadParameters("conflicts_with on suite {} names itself. See documentation: {}"
                                        .format(suite.get_class_name(), DocumentationLinks.THREADING))
                if target_suite is not None:
                    suite_forward.setdefault(suite.get_class_object(), set()).add(target_suite)
                suite_targets |= keys
            for test in suite.get_test_objects():
                if "pr" in test.get_kwargs():
                    old_name.append(_name(test))
                keys = set(suite_targets)
                for target in test.get_parallel_restrictions():
                    resolved, _ = resolve(target, _name(test), True)
                    if resolved == {test.get_function_object()}:
                        raise BadParameters("conflicts_with on test {} names itself. See documentation: {}"
                                            .format(_name(test), DocumentationLinks.THREADING))
                    keys |= resolved
                keys.discard(test.get_function_object())
                if keys:
                    forward[test.get_function_object()] = keys
        conflicts = {}
        for key, others in forward.items():
            for other in others:
                conflicts.setdefault(key, set()).add(other)
                conflicts.setdefault(other, set()).add(key)
        suite_conflicts = {}
        for key, others in suite_forward.items():
            for other in others:
                suite_conflicts.setdefault(key, set()).add(other)
                suite_conflicts.setdefault(other, set()).add(key)
        if old_name:
            warnings.warn("pr= is now called conflicts_with= ({}); pr= keeps working through 1.x and goes no earlier "
                          "than 2.0".format(", ".join(sorted(set(old_name))[:5])), DeprecationWarning, stacklevel=3)
        return ConflictMap(tests, conflicts, suite_conflicts)


def _unknown(kind, owner, target, owner_is_test):
    expected = ("must be function objects decorated with @test(), a suite class, or a name ('Suite' / 'Suite.test')"
                if owner_is_test else
                "must be class objects decorated with @Suite(), a @test() function, or a name ('Suite' / 'Suite.test')")
    return ("conflicts_with on {} {}: targets {}; {!r} (type: {}) doesn't match any. See documentation: {}"
            .format(kind, owner, expected, target, type(target).__name__, DocumentationLinks.THREADING))
