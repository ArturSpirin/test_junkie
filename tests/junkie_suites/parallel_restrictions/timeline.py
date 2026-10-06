import threading
import time

_LOCK = threading.Lock()
_EVENTS = []


def reset():
    with _LOCK:
        _EVENTS.clear()


def record(label, duration=0.3):
    start = time.time()
    time.sleep(duration)
    end = time.time()
    with _LOCK:
        _EVENTS.append((label, start, end))


def events():
    with _LOCK:
        return list(_EVENTS)


def overlaps(a, b):
    return a[1] < b[2] and b[1] < a[2]


def any_overlap(label_a, label_b):
    a_events = [e for e in events() if e[0] == label_a]
    b_events = [e for e in events() if e[0] == label_b]
    for a in a_events:
        for b in b_events:
            if overlaps(a, b):
                return True
    return False


def has_internal_overlap(label):
    same_label = [e for e in events() if e[0] == label]
    for i, a in enumerate(same_label):
        for j, b in enumerate(same_label):
            if i != j and overlaps(a, b):
                return True
    return False


def max_simultaneous():
    # peak number of events running at the same moment. This used to count the events overlapping each event, which
    # over-counts back-to-back events: A overlapping both B and C doesn't mean B and C ran together. That only showed
    # once the scheduler stopped polling every 200ms and started the next suite the moment a slot freed up
    edges = sorted([(start, 1) for _, start, _ in events()] + [(end, -1) for _, _, end in events()])
    best = active = 0
    for _, change in edges:  # at equal times the end (-1) sorts first: back-to-back isn't simultaneous
        active += change
        best = max(best, active)
    return best
