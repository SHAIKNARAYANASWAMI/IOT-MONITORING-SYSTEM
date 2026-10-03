from sqlalchemy.orm import Session

from backend.app.core.algorithms import merge_sort
from backend.app.core.moving_average import MovingAverage
from backend.app.core.priority_queue import AlertPriorityQueue
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.reading_repository import ReadingRepository

SEVERITY_RANK = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}


class AnalyticsService:
    """Uses our own DSA code (not library calls) for reports."""

    def __init__(self, db: Session):
        self.alerts = AlertRepository(db)
        self.readings = ReadingRepository(db)

    def smoothed_temperature(self, device_id: str, window: int = 5, limit: int = 50) -> list[dict]:
        """Moving average of temperature, oldest to newest. O(n) total, O(1) per reading."""
        rows = self.readings.list_for_device(device_id, limit=limit)
        rows.reverse()  # repository returns newest first
        ma = MovingAverage(window)
        result = []
        for r in rows:
            if r.temperature is None:
                continue
            result.append({
                "timestamp": r.timestamp,
                "temperature": r.temperature,
                "smoothed": round(ma.add(r.temperature), 2),
            })
        return result

    def urgent_alerts(self, count: int = 10) -> list:
        """Top `count` active alerts, most severe first (min-heap). O(n log n)."""
        queue = AlertPriorityQueue()
        for alert in self.alerts.list_alerts(limit=1000):
            if alert.status != "RESOLVED":
                queue.push(alert.severity, alert)
        top = []
        while len(top) < count and len(queue) > 0:
            top.append(queue.pop())
        return top

    def alert_report(self) -> list:
        """All alerts: severity first, newest first inside each severity.

        Stable merge sort trick: sort by the secondary key first (newest first),
        then by the primary key (severity). Stability keeps the first order
        inside equal severities.
        """
        alerts = self.alerts.list_alerts(limit=1000)
        by_time = merge_sort(alerts, key=lambda a: -a.created_at.timestamp())
        return merge_sort(by_time, key=lambda a: SEVERITY_RANK[a.severity])