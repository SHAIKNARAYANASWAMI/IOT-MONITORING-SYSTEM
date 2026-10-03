class AlertPriorityQueue:
    """Binary min-heap stored in a list. Most urgent item pops first.

    push O(log n), pop O(log n), peek O(1). Memory O(n).
    Lower priority number = more urgent (CRITICAL=0, WARNING=1, INFO=2).
    Ties are broken by insertion order, so equal-priority alerts stay FIFO.
    """

    PRIORITY = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}

    def __init__(self):
        self._heap: list[tuple[int, int, object]] = []
        self._counter = 0

    def __len__(self) -> int:
        return len(self._heap)

    def push(self, severity: str, item) -> None:
        entry = (self.PRIORITY[severity], self._counter, item)
        self._counter += 1
        self._heap.append(entry)
        self._sift_up(len(self._heap) - 1)

    def peek(self):
        return self._heap[0][2] if self._heap else None

    def pop(self):
        if not self._heap:
            return None
        top = self._heap[0]
        last = self._heap.pop()
        if self._heap:
            self._heap[0] = last
            self._sift_down(0)
        return top[2]

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._heap[i][:2] < self._heap[parent][:2]:
                self._heap[i], self._heap[parent] = self._heap[parent], self._heap[i]
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._heap)
        while True:
            smallest = i
            for child in (2 * i + 1, 2 * i + 2):
                if child < n and self._heap[child][:2] < self._heap[smallest][:2]:
                    smallest = child
            if smallest == i:
                break
            self._heap[i], self._heap[smallest] = self._heap[smallest], self._heap[i]
            i = smallest