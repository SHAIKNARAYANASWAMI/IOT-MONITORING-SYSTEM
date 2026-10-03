from backend.app.core.ring_buffer import RingBuffer


class MovingAverage:
    """Average of the last `window` values using a running sum.

    Each update is O(1): add the new value, subtract the one that fell out of
    the window. Recomputing the whole window every time would be O(window).
    Memory is O(window).
    """

    def __init__(self, window: int):
        self._buffer = RingBuffer(window)
        self._sum = 0.0

    def add(self, value: float) -> float:
        if self._buffer.is_full():
            oldest = self._buffer.oldest()  # O(1)  # O(window), see note below
            self._sum -= oldest
        self._buffer.append(value)
        self._sum += value
        return self.value

    @property
    def value(self) -> float:
        n = len(self._buffer)
        return self._sum / n if n else 0.0