import random

from backend.app.core.algorithms import lower_bound, merge_sort, range_query, upper_bound


def test_merge_sort_basic():
    assert merge_sort([5, 2, 9, 1, 5, 6]) == [1, 2, 5, 5, 6, 9]


def test_merge_sort_empty_and_single():
    assert merge_sort([]) == []
    assert merge_sort([7]) == [7]


def test_merge_sort_matches_builtin_on_random_data():
    data = [random.randint(-100, 100) for _ in range(200)]
    assert merge_sort(data) == sorted(data)


def test_merge_sort_does_not_modify_input():
    data = [3, 1, 2]
    merge_sort(data)
    assert data == [3, 1, 2]


def test_merge_sort_is_stable():
    items = [("b", 1), ("a", 1), ("c", 0), ("d", 1)]
    result = merge_sort(items, key=lambda x: x[1])
    assert result == [("c", 0), ("b", 1), ("a", 1), ("d", 1)]


def test_merge_sort_with_key_descending_via_negation():
    assert merge_sort([1, 3, 2], key=lambda x: -x) == [3, 2, 1]


def test_lower_and_upper_bound():
    data = [1, 3, 3, 3, 5, 7]
    assert lower_bound(data, 3) == 1
    assert upper_bound(data, 3) == 4
    assert lower_bound(data, 0) == 0
    assert lower_bound(data, 100) == 6


def test_bounds_on_empty_list():
    assert lower_bound([], 5) == 0
    assert upper_bound([], 5) == 0


def test_range_query():
    data = [1, 3, 3, 3, 5, 7, 9]
    assert range_query(data, 3, 7) == [3, 3, 3, 5, 7]
    assert range_query(data, 4, 4) == []
    assert range_query(data, 0, 100) == data


def test_range_query_with_key():
    readings = [{"t": 10}, {"t": 20}, {"t": 30}, {"t": 40}]
    result = range_query(readings, 15, 35, key=lambda r: r["t"])
    assert [r["t"] for r in result] == [20, 30]