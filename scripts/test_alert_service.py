from backend.app.database.session import SessionLocal
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.services.alert_service import AlertService

db = SessionLocal()
if DeviceRepository(db).get_by_device_id("TEST-ALERT") is None:
    DeviceRepository(db).add("TEST-ALERT", "Alert test", "Lab")

svc = AlertService(db)
repo = AlertRepository(db)

print("1) bad reading   ->", [a.alert_type for a in svc.check_reading("TEST-ALERT", {"temperature": 62.0, "battery": 7})])
print("2) same again    ->", [a.alert_type for a in svc.check_reading("TEST-ALERT", {"temperature": 63.0, "battery": 7})], "(no duplicates)")
print("3) active now    ->", repo.find_active("TEST-ALERT", "HIGH_TEMPERATURE") is not None)
svc.check_reading("TEST-ALERT", {"temperature": 30.0, "battery": 80})
print("4) after normal  ->", repo.find_active("TEST-ALERT", "HIGH_TEMPERATURE"), "(auto-resolved)")