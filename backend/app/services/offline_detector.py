import threading
from datetime import datetime, timedelta

from backend.app.config import get_settings
from backend.app.database.session import SessionLocal
from backend.app.logging_config import get_logger
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository

logger = get_logger("services.offline")


class OfflineDetector:
    """Background thread: marks devices OFFLINE if no data arrives within the timeout."""

    def __init__(self, check_interval: float = 5.0):
        self.timeout = get_settings().offline_timeout_seconds
        self.check_interval = check_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="offline-detector", daemon=True)

    def start(self) -> None:
        self._thread.start()
        logger.info("Offline detector started (timeout=%ss)", self.timeout)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=3)

    def _run(self) -> None:
        # Event.wait() doubles as an interruptible sleep.
        while not self._stop.wait(self.check_interval):
            try:
                self.check_once()
            except Exception:
                logger.exception("Offline check failed")

    def check_once(self, now: datetime | None = None) -> list[str]:
        """One scan over all devices. Returns the ids that just went offline."""
        now = now or datetime.utcnow()
        cutoff = now - timedelta(seconds=self.timeout)
        went_offline = []
        db = SessionLocal()
        try:
            devices = DeviceRepository(db)
            alerts = AlertRepository(db)
            for device in devices.list_all():
                if device.status == "OFFLINE" or device.last_seen is None:
                    continue
                if device.last_seen < cutoff:
                    devices.update_status(device.device_id, "OFFLINE")
                    if alerts.find_active(device.device_id, "DEVICE_OFFLINE") is None:
                        silent_for = (now - device.last_seen).total_seconds()
                        alerts.add(device.device_id, "DEVICE_OFFLINE", "CRITICAL", round(silent_for, 1), self.timeout)
                    logger.warning("Device %s is OFFLINE (no data for >%ss)", device.device_id, self.timeout)
                    went_offline.append(device.device_id)
        finally:
            db.close()
        return went_offline