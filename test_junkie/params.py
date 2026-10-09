"""
The text Test Junkie keys a parameter's results by: str(value), or the label given with ids=.

Results, meta, reports and --rerun all find a parameter by this text, so two parameters of the same test (or two
suite parameters) must not share it. ids= exists for objects whose str() you can't change.
"""
import threading

_PRIMITIVES = (str, bytes, int, float, complex, bool, type(None))
_IDS = {}  # id(parameter object) -> label, for the current run
_LOCK = threading.Lock()


def param_key(value):
    """The text results for this parameter are recorded under."""
    if not isinstance(value, _PRIMITIVES):
        label = _IDS.get(id(value))
        if label is not None:
            return label
    return str(value)


def register(parameters, ids):
    """
    Labels each parameter object with its id from ids= (a list, or a function of the parameter). Primitives keep
    str(): they're shared objects, so a label on 1 would leak to every other parameter that is 1.
    """
    if ids is None or not isinstance(parameters, list):
        return
    labels = ids if isinstance(ids, list) else [ids(parameter) for parameter in parameters]
    if len(labels) != len(parameters):
        return  # reported by Runner's parameter validation
    with _LOCK:
        for parameter, label in zip(parameters, labels):
            if not isinstance(parameter, _PRIMITIVES) and isinstance(label, str):
                _IDS[id(parameter)] = label


def reset():
    with _LOCK:
        _IDS.clear()


def duplicates(parameters):
    """[(text, [values...])] for every text more than one parameter would be recorded under"""
    seen = {}
    for parameter in parameters:
        seen.setdefault(param_key(parameter), []).append(parameter)
    return [(text, values) for text, values in seen.items() if len(values) > 1]
