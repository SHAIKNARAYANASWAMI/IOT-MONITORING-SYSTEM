from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.models import SensorReading


class ReadingRepository:
    """The only place that talks to the sensor_readings table."""

    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        device_id: str,
        timestamp: datetime | None = None,
        temperature: float | None = None,
        humidity: float | None = None,
        voltage: float | None = None,
        current: float | None = None,
        pressure: float | None = None,
        battery: int | None = None,
    ) -> SensorReading:
        reading = SensorReading(
            device_id=device_id,
            timestamp=timestamp or datetime.utcnow(),
            temperature=temperature,
            humidity=humidity,
            voltage=voltage,
            current=current,
            pressure=pressure,
            battery=battery,
        )
        self.db.add(reading)
        self.db.commit()
        self.db.refresh(reading)
        return reading

    def get_latest(self, device_id: str) -> SensorReading | None:
        stmt = (
            select(SensorReading)
            .where(SensorReading.device_id == device_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_device(self, device_id: str, limit: int = 100) -> list[SensorReading]:
        """Newest first, limited so we never load the whole table."""
        stmt = (
            select(SensorReading)
            .where(SensorReading.device_id == device_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())