from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.models import Alert


class AlertRepository:
    """The only place that talks to the alerts table."""

    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        device_id: str,
        alert_type: str,
        severity: str,
        actual_value: float | None = None,
        threshold_value: float | None = None,
    ) -> Alert:
        alert = Alert(
            device_id=device_id,
            alert_type=alert_type,
            severity=severity,
            actual_value=actual_value,
            threshold_value=threshold_value,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def get(self, alert_id: int) -> Alert | None:
        return self.db.get(Alert, alert_id)

    def find_active(self, device_id: str, alert_type: str) -> Alert | None:
        """Active = not RESOLVED. Used to avoid creating duplicate alerts."""
        stmt = select(Alert).where(
            Alert.device_id == device_id,
            Alert.alert_type == alert_type,
            Alert.status != "RESOLVED",
        )
        return self.db.execute(stmt).scalars().first()

    def list_alerts(self, status: str | None = None, limit: int = 100) -> list[Alert]:
        stmt = select(Alert).order_by(Alert.created_at.desc()).limit(limit)
        if status:
            stmt = stmt.where(Alert.status == status)
        return list(self.db.execute(stmt).scalars().all())

    def acknowledge(self, alert_id: int) -> Alert | None:
        alert = self.get(alert_id)
        if alert is None:
            return None
        if alert.status == "OPEN":
            alert.status = "ACKNOWLEDGED"
            alert.acknowledged_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(alert)
        return alert

    def resolve(self, alert_id: int) -> Alert | None:
        alert = self.get(alert_id)
        if alert is None:
            return None
        if alert.status != "RESOLVED":
            alert.status = "RESOLVED"
            alert.resolved_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(alert)
        return alert