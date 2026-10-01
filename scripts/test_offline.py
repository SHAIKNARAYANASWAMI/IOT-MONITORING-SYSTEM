from datetime import datetime, timedelta

from backend.app.database.session import SessionLocal
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.services.offline_detector import OfflineDetector

db = SessionLocal()
devices = DeviceRepository(db)
if devices.get_by_device_id("TEST-OFFLINE") is None:
    devices.add("TEST-OFFLINE", "Offline test", "Lab")

# Pretend this device last sent data 60 seconds ago.
devices.update_status("TEST-OFFLINE", "ONLINE", last_seen=datetime.utcnow() - timedelta(seconds=60))

result = OfflineDetector().check_once()
print("went offline:", result)
print("TEST-OFFLINE detected:", "TEST-OFFLINE" in result)
print("alert exists:", AlertRepository(db).find_active("TEST-OFFLINE", "DEVICE_OFFLINE") is not None)