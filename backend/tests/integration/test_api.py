import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.threshold_repository import ThresholdRepository


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


# ---------- health ----------
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------- auth ----------
def test_login_success_returns_token(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_401(client):
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_write_without_token_401(client):
    r = client.post("/devices", json={"device_id": "D1"})
    assert r.status_code == 401


def test_write_with_bad_token_401(client):
    r = client.post("/devices", json={"device_id": "D1"}, headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


# ---------- devices ----------
def test_register_device_201(client, auth_headers):
    r = client.post("/devices", json={"device_id": "D1", "name": "Boiler", "location": "Plant A"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["device_id"] == "D1"


def test_register_duplicate_device_409(client, auth_headers):
    client.post("/devices", json={"device_id": "D1"}, headers=auth_headers)
    r = client.post("/devices", json={"device_id": "D1"}, headers=auth_headers)
    assert r.status_code == 409


def test_register_invalid_device_id_422(client, auth_headers):
    r = client.post("/devices", json={"device_id": "bad id!"}, headers=auth_headers)
    assert r.status_code == 422


def test_get_unknown_device_404(client):
    assert client.get("/devices/NOPE").status_code == 404


def test_list_devices(client, db):
    DeviceRepository(db).add("D1")
    DeviceRepository(db).add("D2")
    r = client.get("/devices")
    assert r.status_code == 200
    assert [d["device_id"] for d in r.json()] == ["D1", "D2"]


# ---------- telemetry ----------
def test_telemetry_stored_201(client):
    r = client.post("/telemetry", json={"device_id": "D1", "temperature": 35.5, "battery": 80})
    assert r.status_code == 201
    readings = client.get("/devices/D1/readings").json()
    assert len(readings) == 1
    assert readings[0]["temperature"] == 35.5


def test_telemetry_invalid_value_422(client):
    r = client.post("/telemetry", json={"device_id": "D1", "temperature": 9999})
    assert r.status_code == 422


def test_readings_for_unknown_device_404(client):
    assert client.get("/devices/NOPE/readings").status_code == 404


# ---------- alerts ----------
def test_alert_created_via_telemetry_and_listed(client, db):
    ThresholdRepository(db).upsert("temperature", 5, 50, "CRITICAL")
    client.post("/telemetry", json={"device_id": "D1", "temperature": 75})
    alerts = client.get("/alerts?status=OPEN").json()
    assert [a["alert_type"] for a in alerts] == ["HIGH_TEMPERATURE"]


def test_acknowledge_alert_requires_auth(client, db):
    DeviceRepository(db).add("D1")
    alert = AlertRepository(db).add("D1", "HIGH_TEMPERATURE", "CRITICAL", 62, 50)
    assert client.put(f"/alerts/{alert.id}/acknowledge").status_code == 401


def test_acknowledge_alert_200(client, auth_headers, db):
    DeviceRepository(db).add("D1")
    alert = AlertRepository(db).add("D1", "HIGH_TEMPERATURE", "CRITICAL", 62, 50)
    r = client.put(f"/alerts/{alert.id}/acknowledge", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["status"] == "ACKNOWLEDGED"


def test_acknowledge_unknown_alert_404(client, auth_headers):
    assert client.put("/alerts/9999/acknowledge", headers=auth_headers).status_code == 404


def test_alerts_invalid_status_filter_422(client):
    assert client.get("/alerts?status=BOGUS").status_code == 422


# ---------- thresholds ----------
def test_set_threshold_200(client, auth_headers):
    r = client.post(
        "/thresholds",
        json={"metric": "temperature", "min_value": 5, "max_value": 60, "severity": "CRITICAL"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["max_value"] == 60


def test_threshold_min_greater_than_max_422(client, auth_headers):
    r = client.post("/thresholds", json={"metric": "temperature", "min_value": 80, "max_value": 10}, headers=auth_headers)
    assert r.status_code == 422


def test_threshold_unknown_metric_422(client, auth_headers):
    r = client.post("/thresholds", json={"metric": "bogus", "max_value": 10}, headers=auth_headers)
    assert r.status_code == 422


def test_threshold_unknown_device_404(client, auth_headers):
    r = client.post("/thresholds", json={"metric": "temperature", "max_value": 60, "device_id": "NOPE"}, headers=auth_headers)
    assert r.status_code == 404