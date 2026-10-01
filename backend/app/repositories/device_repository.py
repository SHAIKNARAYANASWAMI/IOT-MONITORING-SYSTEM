from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.models import Device


class DeviceRepository:
    """The only place that talks to the devices table."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, device_id: str, name: str = "", location: str = "") -> Device:
        device = Device(device_id=device_id, name=name, location=location)
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_by_device_id(self, device_id: str) -> Device | None:
        stmt = select(Device).where(Device.device_id == device_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Device]:
        stmt = select(Device).order_by(Device.device_id)
        return list(self.db.execute(stmt).scalars().all())

    def update_status(self, device_id: str, status: str, last_seen: datetime | None = None) -> None:
        device = self.get_by_device_id(device_id)
        if device is None:
            return
        device.status = status
        if last_seen is not None:
            device.last_seen = last_seen
        self.db.commit()