"""
Retry policies: which failures to retry, how many times, and how long to wait in between.

    class Flaky(RetryPolicy):
        no_retry_on = [PermissionError]
        when = [When(TimeoutError, attempts=3, delay=1),
                When(message="503", attempts=2, delay=20, backoff=2)]

    @test(retry=Flaky)

A policy decides from the failures a test has had so far, so one policy can be shared by every test and parameter.
"""
import random
import re

from test_junkie.errors import BadParameters

_PATTERN = type(re.compile(""))
_NUMBER = (int, float)


def _is_exception_type(value):
    return isinstance(value, type) and issubclass(value, BaseException)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _label(value):
    return getattr(value, "__name__", None) or str(value)


def _check_exceptions(owner, field, value):
    for item in _as_list(value):
        if not _is_exception_type(item):
            raise BadParameters("{}.{} takes exception classes, got {!r}".format(owner, field, item))
    return tuple(_as_list(value))


def _check_messages(owner, field, value):
    for item in _as_list(value):
        if not isinstance(item, (str, _PATTERN)):
            raise BadParameters("{}.{} takes text to find in the error, or re.compile(...), got {!r}"
                                .format(owner, field, item))
    return tuple(_as_list(value))


def _check_number(owner, field, value, minimum, allow_none=True, integer=False):
    if value is None and allow_none:
        return None
    kinds = int if integer else _NUMBER
    if isinstance(value, bool) or not isinstance(value, kinds) or value < minimum:
        raise BadParameters("{}.{} must be {} {} or more, got {!r}"
                            .format(owner, field, "a whole number" if integer else "a number", minimum, value))
    return value


def _chain(error):
    """The error, then whatever caused it (__cause__, then __context__), without looping."""
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        yield error
        error = error.__cause__ or error.__context__


class When(object):
    """
    One kind of failure and how to retry it. Matches when the error is one of `exceptions` (any, if none given)
    and contains one of `message` (any, if none given). Fields left as None come from the policy.
    """

    def __init__(self, *exceptions, message=None, attempts=None, delay=None, backoff=None, max_delay=None,
                 jitter=None, name=None):
        owner = "When"
        self.exceptions = _check_exceptions(owner, "exceptions", list(exceptions))
        self.messages = _check_messages(owner, "message", message)
        self.attempts = _check_number(owner, "attempts", attempts, 1, integer=True)
        self.delay = _check_number(owner, "delay", delay, 0)
        self.backoff = _check_number(owner, "backoff", backoff, 1)
        self.max_delay = _check_number(owner, "max_delay", max_delay, 0)
        self.jitter = _check_number(owner, "jitter", jitter, 0)
        if name is not None and not isinstance(name, str):
            raise BadParameters("When.name must be text, got {!r}".format(name))
        self.name = name

    def matches(self, error, chain=False):
        candidates = list(_chain(error)) if chain else [error]
        for candidate in candidates:
            if self.exceptions and not isinstance(candidate, self.exceptions):
                continue
            if self.messages and not _message_matches(self.messages, candidate):
                continue
            return True
        return False

    def label(self):
        if self.name:
            return self.name
        parts = [_label(e) for e in self.exceptions]
        parts += ['"{}"'.format(m.pattern if isinstance(m, _PATTERN) else m) for m in self.messages]
        return " or ".join(parts) if parts else "any failure"

    def __repr__(self):
        return "<When {}>".format(self.label())


def _message_matches(messages, error):
    text = str(error)
    for message in messages:
        if isinstance(message, _PATTERN):
            if message.search(text):
                return True
        elif message in text:
            return True
    return False


class Decision(object):
    """What a policy decided after a failed run."""

    def __init__(self, retry, when=None, delay=0.0, run=1, of=1, reason=None):
        self.retry = retry
        self.when = when
        self.delay = delay
        self.run = run  # the run that just failed, counting from 1
        self.of = of  # how many runs the matched condition allows
        self.reason = reason

    def __bool__(self):
        return self.retry

    def __repr__(self):
        return "<Decision retry={} when={} delay={} run={}/{}>".format(
            self.retry, self.when, self.delay, self.run, self.of)


_FIELDS = ("attempts", "retry_on", "no_retry_on", "message", "delay", "backoff", "max_delay", "jitter", "chain",
           "when")


class RetryPolicy(object):
    """
    Subclass it and set the fields you need; pass the class (or an instance with overrides) to @test(retry=...)
    or @Suite(retry_policy=...).

    attempts:    most runs in total, the first included (1 = no retries). Without `when`, retries any failure.
    retry_on:    exception classes worth retrying; others aren't retried. Empty = any.
    no_retry_on: exception classes never retried. Always wins.
    message:     text to find in the error (plain substring, case-sensitive), re.compile(...) for a pattern,
                 or a list of either.
    delay:       seconds to wait before a retry. backoff multiplies it each time (2 = 1s, 2s, 4s...),
                 max_delay caps it, jitter adds up to that many random seconds.
    chain:       also look at what caused the error (`raise ... from ...` and errors raised while handling another).
    when:        a list of When(...) for different kinds of failure. The first one that matches decides, and each
                 has its own budget of attempts.
    """

    attempts = None
    retry_on = ()
    no_retry_on = ()
    message = None
    delay = 0
    backoff = 1
    max_delay = None
    jitter = 0
    chain = False
    when = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._validate(cls, cls.__name__)

    def __init__(self, **overrides):
        unknown = sorted(set(overrides) - set(_FIELDS))
        if unknown:
            raise BadParameters("{} doesn't take {}; it takes {}".format(
                type(self).__name__, ", ".join(unknown), ", ".join(_FIELDS)))
        for field, value in overrides.items():
            setattr(self, field, value)
        self._validate(self, type(self).__name__)

    @staticmethod
    def _validate(target, owner):
        attempts = _check_number(owner, "attempts", target.attempts, 1, integer=True)
        retry_on = _check_exceptions(owner, "retry_on", target.retry_on)
        no_retry_on = _check_exceptions(owner, "no_retry_on", target.no_retry_on)
        messages = _check_messages(owner, "message", target.message)
        delay = _check_number(owner, "delay", target.delay, 0, allow_none=False)
        backoff = _check_number(owner, "backoff", target.backoff, 1, allow_none=False)
        max_delay = _check_number(owner, "max_delay", target.max_delay, 0)
        jitter = _check_number(owner, "jitter", target.jitter, 0, allow_none=False)
        if not isinstance(target.chain, bool):
            raise BadParameters("{}.chain must be True or False, got {!r}".format(owner, target.chain))
        whens = _as_list(target.when)
        for item in whens:
            if not isinstance(item, When):
                raise BadParameters("{}.when takes a list of When(...), got {!r}".format(owner, item))
            if item.attempts is None and attempts is None:
                raise BadParameters("{}.when: {!r} has no attempts, and neither does {}".format(owner, item, owner))
        if whens and (retry_on or messages):
            raise BadParameters("{} sets both when and retry_on/message; put those in a When(...)".format(owner))
        if not whens:
            whens = [When(*retry_on, message=list(messages) or None)]
        if attempts is None:
            attempts = None if any(w.attempts for w in whens) else 1
        target._conditions = tuple(whens)
        target._attempts = attempts
        target._no_retry_on = no_retry_on
        target._delay, target._backoff, target._max_delay, target._jitter = delay, backoff, max_delay, jitter

    # -- the decision -------------------------------------------------------------------------------------------

    def name(self):
        return type(self).__name__

    def _get(self, when, field):
        value = getattr(when, field)
        return getattr(self, "_" + field) if value is None else value

    def _match(self, error):
        for when in self._conditions:
            if when.matches(error, chain=self.chain):
                return when
        return None

    def _excluded(self, error):
        if not self._no_retry_on:
            return False
        candidates = list(_chain(error)) if self.chain else [error]
        return any(isinstance(candidate, self._no_retry_on) for candidate in candidates)

    def qualifies(self, error):
        """Whether this error is worth retrying at all (used to pick tests for a suite's retry pass)."""
        return error is not None and not self._excluded(error) and self._match(error) is not None

    def decide(self, errors):
        """
        errors: the error of every run so far, oldest first; the last one just failed.
        Returns a Decision: whether to run again, which When matched and how long to wait first.
        """
        errors = list(errors)
        run = len(errors)
        error = errors[-1] if errors else None
        if error is None:
            return Decision(False, run=run, of=run, reason="no error")
        if self._excluded(error):
            return Decision(False, run=run, of=run, reason="no_retry_on")
        when = self._match(error)
        if when is None:
            return Decision(False, run=run, of=run, reason="no condition matched")
        allowed = self._get(when, "attempts")
        if self._attempts is not None:
            allowed = min(allowed, self._attempts) if allowed is not None else self._attempts
        # each condition counts only the failures it matched (first match wins for every past failure too)
        matched = sum(1 for past in errors if self._match(past) is when)
        if matched >= allowed or (self._attempts is not None and run >= self._attempts):
            return Decision(False, when=when, run=matched, of=allowed, reason="out of attempts")
        return Decision(True, when=when, delay=self.wait(when, matched), run=matched, of=allowed)

    def wait(self, when, matched):
        """Seconds to wait after the `matched`-th failure that `when` matched."""
        delay = self._get(when, "delay") * (self._get(when, "backoff") ** (matched - 1))
        cap = self._get(when, "max_delay")
        if cap is not None:
            delay = min(delay, cap)
        jitter = self._get(when, "jitter")
        if jitter:
            delay += random.uniform(0, jitter)
        return delay

    def total_attempts(self):
        """The most runs this policy can give a test, for counts and reports (None = no fixed cap)."""
        if self._attempts is not None:
            return self._attempts
        budgets = [w.attempts for w in self._conditions if w.attempts is not None]
        return sum(b - 1 for b in budgets) + 1 if budgets else None

    def __repr__(self):
        return "<{} attempts={} when={}>".format(self.name(), self._attempts, list(self._conditions))


class _LegacyRetry(RetryPolicy):
    """What @test(retry=N, retry_on=[...], no_retry_on=[...]) has always meant, as a policy."""

    def name(self):
        return "retry"


def resolve(value, owner):
    """Turn whatever was passed as a retry policy into a RetryPolicy instance (or None)."""
    if value is None:
        return None
    if isinstance(value, type) and issubclass(value, RetryPolicy):
        return value()
    if isinstance(value, RetryPolicy):
        return value
    raise BadParameters("{} takes a RetryPolicy subclass or instance, got {!r}".format(owner, value))
