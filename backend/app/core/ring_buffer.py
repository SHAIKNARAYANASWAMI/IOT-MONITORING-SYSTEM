class RingBuffer:
    """Fixed-size circular buffer (sliding window).

    Keeps only the newest `capacity` items. When full, a new item overwrites
    the oldest one. Insert is O(1); memory is O(capacity) and never grows.
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._data = [None] * capacity   # pre-allocated array
        self._start = 0                  # index of the oldest item
        self._size = 0                   # how many items are stored

    def __len__(self) -> int:
        return self._size

    def is_full(self) -> bool:
        return self._size == self.capacity

    def append(self, item) -> None:
        """O(1): write at the next free slot, or overwrite the oldest."""
        end = (self._start + self._size) % self.capacity
        if self._size < self.capacity:
            self._data[end] = item
            self._size += 1
        else:
            self._data[self._start] = item
            self._start = (self._start + 1) % self.capacity

    def to_list(self) -> list:
        """Items from oldest to newest. O(n)."""
        return [self._data[(self._start + i) % self.capacity] for i in range(self._size)]

    def latest(self):
        """Newest item, or None if empty. O(1)."""
        if self._size == 0:
            return None
        return self._data[(self._start + self._size - 1) % self.capacity]