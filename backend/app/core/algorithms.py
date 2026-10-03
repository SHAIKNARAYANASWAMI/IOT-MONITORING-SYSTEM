def merge_sort(items: list, key=lambda x: x) -> list:
    """Stable merge sort. Time O(n log n) always, extra space O(n).

    Stable means equal items keep their original order, which matters when
    sorting alerts by severity but wanting newest-first inside each severity.
    """
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort(items[:mid], key)
    right = merge_sort(items[mid:], key)
    return _merge(left, right, key)


def _merge(left: list, right: list, key) -> list:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        # <= (not <) keeps the sort stable
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def lower_bound(sorted_items: list, target, key=lambda x: x) -> int:
    """Index of the first item whose key is >= target. Time O(log n), space O(1).

    Returns len(sorted_items) if every item is smaller than target.
    """
    lo, hi = 0, len(sorted_items)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) < target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def upper_bound(sorted_items: list, target, key=lambda x: x) -> int:
    """Index of the first item whose key is > target. Time O(log n)."""
    lo, hi = 0, len(sorted_items)
    while lo < hi:
        mid = (lo + hi) // 2
        if key(sorted_items[mid]) <= target:
            lo = mid + 1
        else:
            hi = mid
    return lo


def range_query(sorted_items: list, low, high, key=lambda x: x) -> list:
    """All items with low <= key <= high from a sorted list.

    Two binary searches find the boundaries (O(log n)), then slicing copies
    only the k matching items, so total time is O(log n + k).
    """
    start = lower_bound(sorted_items, low, key)
    end = upper_bound(sorted_items, high, key)
    return sorted_items[start:end]