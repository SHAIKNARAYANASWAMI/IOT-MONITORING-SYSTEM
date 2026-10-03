from backend.app.core.moving_average import MovingAverage
from backend.app.core.priority_queue import AlertPriorityQueue
from backend.app.core.ring_buffer import RingBuffer


def test_oldest():
    rb = RingBuffer(3)
    assert rb.oldest() is None
    for i in (1, 2, 3, 4):
        rb.append(i)
    assert rb.oldest() == 2


def test_moving_average_partial_window():
    ma = MovingAverage(3)
    assert ma.add(10) == 10
    assert ma.add(20) == 15


def test_moving_average_slides():
    ma = MovingAverage(3)
    for v in (10, 20, 30):
        ma.add(v)
    assert ma.add(40) == 30  # window is now 20, 30, 40


def test_moving_average_empty_is_zero():
    assert MovingAverage(3).value == 0.0


def test_priority_queue_critical_first():
    q = AlertPriorityQueue()
    q.push("INFO", "a")
    q.push("CRITICAL", "b")
    q.push("WARNING", "c")
    assert [q.pop(), q.pop(), q.pop()] == ["b", "c", "a"]


def test_priority_queue_fifo_within_same_severity():
    q = AlertPriorityQueue()
    for name in ("first", "second", "third"):
        q.push("WARNING", name)
    assert [q.pop(), q.pop(), q.pop()] == ["first", "second", "third"]


def test_priority_queue_empty():
    q = AlertPriorityQueue()
    assert q.pop() is None
    assert q.peek() is None


def test_priority_queue_many_items_sorted_output():
    q = AlertPriorityQueue()
    order = ["INFO", "CRITICAL", "WARNING"] * 20
    for i, sev in enumerate(order):
        q.push(sev, (sev, i))
    popped = [q.pop() for _ in range(len(order))]
    ranks = [AlertPriorityQueue.PRIORITY[s] for s, _ in popped]
    assert ranks == sorted(ranks)