from datetime import datetime, timedelta

from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.reading_repository import ReadingRepository
from backend.app.repositories.threshold_repository import ThresholdRepository
from backend.app.services.alert_service import AlertService
from backend.app.services.ingestion_service import IngestionService
from backend.app.services.offline_detector import OfflineDetector


def seed_thresholds(db):
    repo = ThresholdRepository(db)
    repo.upsert("temperature", 5, 50, "CRITICAL")
    repo.upsert("battery", 20, None, "WARNING")


# ---------- repositories ----------
def test_device_add_and_get(db):
    repo = DeviceRepository(db)
    repo.add("D1", "Boiler", "Plant A")
    assert repo.get_by_device_id("D1").name == "Boiler"
    assert repo.get_by_device_id("NOPE") is None


def test_reading_latest_returns_newest(db):
    DeviceRepository(db).add("D1")
    readings = ReadingRepository(db)
    readings.add("D1", timestamp=datetime(2026, 1, 1, 10, 0), temperature=20)
    readings.add("D1", timestamp=datetime(2026, 1, 1, 10, 5), temperature=25)
    assert readings.get_latest("D1").temperature == 25


def test_threshold_upsert_updates_instead_of_duplicating(db):
    repo = ThresholdRepository(db)
    repo.upsert("temperature", 5, 50, "CRITICAL")
    repo.upsert("temperature", 5, 55, "CRITICAL")
    assert len(repo.list_all()) == 1
    assert repo.get("temperature").max_value == 55


def test_device_specific_threshold_wins_over_global(db):
    DeviceRepository(db).add("D1")
    repo = ThresholdRepository(db)
    repo.upsert("temperature", 5, 50, "CRITICAL")
    repo.upsert("temperature", 5, 80, "CRITICAL", device_id="D1")
    assert repo.get_effective("temperature", "D1").max_value == 80
    assert repo.get_effective("temperature", "OTHER").max_value == 50


# ---------- alert service ----------
def test_alert_created_for_bad_reading(db):
    DeviceRepository(db).add("D1")
    seed_thresholds(db)
    created = AlertService(db).check_reading("D1", {"temperature": 62.0, "battery": 7})
    assert sorted(a.alert_type for a in created) == ["HIGH_TEMPERATURE", "LOW_BATTERY"]


def test_no_duplicate_alert_while_condition_continues(db):
    DeviceRepository(db).add("D1")
    seed_thresholds(db)
    svc = AlertService(db)
    svc.check_reading("D1", {"temperature": 62.0})
    again = svc.check_reading("D1", {"temperature": 65.0})
    assert again == []
    assert len(AlertRepository(db).list_alerts()) == 1


def test_alert_auto_resolves_when_normal(db):
    DeviceRepository(db).add("D1")
    seed_thresholds(db)
    svc = AlertService(db)
    svc.check_reading("D1", {"temperature": 62.0})
    svc.check_reading("D1", {"temperature": 30.0})
    assert AlertRepository(db).find_active("D1", "HIGH_TEMPERATURE") is None


def test_acknowledge_then_resolve(db):
    DeviceRepository(db).add("D1")
    repo = AlertRepository(db)
    alert = repo.add("D1", "HIGH_TEMPERATURE", "CRITICAL", 62, 50)
    assert repo.acknowledge(alert.id).status == "ACKNOWLEDGED"
    assert repo.resolve(alert.id).status == "RESOLVED"


def test_resolved_alert_cannot_be_acknowledged(db):
    DeviceRepository(db).add("D1")
    repo = AlertRepository(db)
    alert = repo.add("D1", "HIGH_TEMPERATURE", "CRITICAL", 62, 50)
    repo.resolve(alert.id)
    assert repo.acknowledge(alert.id).status == "RESOLVED"


# ---------- offline detector ----------
def test_silent_device_goes_offline_and_gets_alert(db):
    devices = DeviceRepository(db)
    devices.add("D1")
    devices.update_status("D1", "ONLINE", last_seen=datetime.utcnow() - timedelta(seconds=120))
    went_offline = OfflineDetector().check_once()
    assert went_offline == ["D1"]
    assert AlertRepository(db).find_active("D1", "DEVICE_OFFLINE") is not None


def test_recent_device_stays_online(db):
    devices = DeviceRepository(db)
    devices.add("D1")
    devices.update_status("D1", "ONLINE", last_seen=datetime.utcnow())
    assert OfflineDetector().check_once() == []


def test_offline_alert_resolves_when_data_returns(db):
    devices = DeviceRepository(db)
    devices.add("D1")
    devices.update_status("D1", "ONLINE", last_seen=datetime.utcnow() - timedelta(seconds=120))
    OfflineDetector().check_once()
    AlertService(db).check_reading("D1", {"temperature": 30.0})
    assert AlertRepository(db).find_active("D1", "DEVICE_OFFLINE") is None


# ---------- ingestion pipeline ----------
def test_ingestion_stores_valid_message(db):
    seed_thresholds(db)
    svc = IngestionService()
    ok = svc.process({"device_id": "D1", "temperature": 35.5, "battery": 80})
    assert ok is True
    assert DeviceRepository(db).get_by_device_id("D1").status == "ONLINE"
    assert ReadingRepository(db).get_latest("D1").temperature == 35.5


def test_ingestion_rejects_invalid_message(db):
    svc = IngestionService()
    assert svc.process({"device_id": "D1", "temperature": 9999}) is False
    assert svc.rejected == 1
    assert DeviceRepository(db).get_by_device_id("D1") is None


def test_ingestion_creates_alert_for_bad_reading(db):
    seed_thresholds(db)
    IngestionService().process({"device_id": "D1", "temperature": 70, "battery": 5})
    assert AlertRepository(db).find_active("D1", "HIGH_TEMPERATURE") is not None
    assert AlertRepository(db).find_active("D1", "LOW_BATTERY") is not None