from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.models import Threshold


class ThresholdRepository:
    """The only place that talks to the thresholds table."""

    def __init__(self, db: Session):
        self.db = db

    def upsert(
        self,
        metric: str,
        min_value: float | None = None,
        max_value: float | None = None,
        severity: str = "WARNING",
        device_id: str | None = None,
    ) -> Threshold:
        """Update the threshold if it exists, otherwise create it."""
        threshold = self.get(metric, device_id)
        if threshold is None:
            threshold = Threshold(metric=metric, device_id=device_id)
            self.db.add(threshold)
        threshold.min_value = min_value
        threshold.max_value = max_value
        threshold.severity = severity
        self.db.commit()
        self.db.refresh(threshold)
        return threshold

    def get(self, metric: str, device_id: str | None = None) -> Threshold | None:
        stmt = select(Threshold).where(Threshold.metric == metric)
        if device_id is None:
            stmt = stmt.where(Threshold.device_id.is_(None))
        else:
            stmt = stmt.where(Threshold.device_id == device_id)
        return self.db.execute(stmt).scalars().first()

    def get_effective(self, metric: str, device_id: str) -> Threshold | None:
        """Device-specific threshold wins; otherwise fall back to the global one."""
        return self.get(metric, device_id) or self.get(metric, None)

    def list_all(self) -> list[Threshold]:
        stmt = select(Threshold).order_by(Threshold.metric)
        return list(self.db.execute(stmt).scalars().all())