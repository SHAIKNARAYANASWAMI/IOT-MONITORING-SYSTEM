from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.reading_repository import ReadingRepository
from backend.app.services.analytics_service import AnalyticsService


def test_smoothed_temperature_uses_moving_average(db):
    DeviceRepository(db).add("D1")
    base = datetime(2026, 1, 1, 10, 0)
    for i, t in enumerate([10, 20, 30, 40]):
        ReadingRepository(db).add("D1", timestamp=base + timedelta(minutes=i), temperature=t)
    result = AnalyticsService(db).smoothed_temperature("D1", window=3)
    assert [r["smoothed"] for r in result] == [10.0, 15.0, 20.0, 30.0]


def test_urgent_alerts_critical_first_and_skips_resolved(db):
    DeviceRepository(db).add("D1")
    repo = AlertRepository(db)
    repo.add("D1", "LOW_BATTERY", "WARNING", 5, 20)
    repo.add("D1", "HIGH_TEMPERATURE", "CRITICAL", 70, 50)
    done = repo.add("D1", "HIGH_CURRENT", "CRITICAL", 15, 10)
    repo.resolve(done.id)
    result = AnalyticsService(db).urgent_alerts()
    assert [a.alert_type for a in result] == ["HIGH_TEMPERATURE", "LOW_BATTERY"]


def test_alert_report_severity_then_newest_first(db):
    DeviceRepository(db).add("D1")
    repo = AlertRepository(db)
    repo.add("D1", "WARN_OLD", "WARNING", 1, 1)
    repo.add("D1", "CRIT_OLD", "CRITICAL", 1, 1)
    repo.add("D1", "CRIT_NEW", "CRITICAL", 1, 1)
    repo.add("D1", "INFO_ONE", "INFO", 1, 1)
    types = [a.alert_type for a in AnalyticsService(db).alert_report()]
    assert types[0] == "CRIT_NEW"
    assert types[1] == "CRIT_OLD"
    assert types[2] == "WARN_OLD"
    assert types[3] == "INFO_ONE"


def test_analytics_endpoints():
    client = TestClient(app)
    assert client.get("/analytics/urgent-alerts").status_code == 200
    assert client.get("/analytics/alert-report").status_code == 200
    assert client.get("/analytics/devices/NOPE/smoothed-temperature").status_code == 404