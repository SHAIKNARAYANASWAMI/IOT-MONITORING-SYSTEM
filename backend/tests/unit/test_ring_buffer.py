import pytest

from backend.app.core.ring_buffer import RingBuffer


def test_stores_items_in_order():
    rb = RingBuffer(3)
    rb.append(1)
    rb.append(2)
    assert rb.to_list() == [1, 2]
    assert len(rb) == 2


def test_overwrites_oldest_when_full():
    rb = RingBuffer(3)
    for i in range(1, 6):
        rb.append(i)
    assert rb.to_list() == [3, 4, 5]
    assert rb.is_full()


def test_latest():
    rb = RingBuffer(3)
    assert rb.latest() is None
    rb.append(10)
    rb.append(20)
    assert rb.latest() == 20


def test_size_never_exceeds_capacity():
    rb = RingBuffer(2)
    for i in range(100):
        rb.append(i)
    assert len(rb) == 2
    assert rb.to_list() == [98, 99]


def test_invalid_capacity_rejected():
    with pytest.raises(ValueError):
        RingBuffer(0)