from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.app.schemas.telemetry import TelemetryIn


def test_valid_message_is_accepted():
    m = TelemetryIn(device_id="DEVICE-001", temperature=35.5, battery=84)
    assert m.temperature == 35.5
    assert m.status == "ONLINE"


def test_utc_timestamp_becomes_naive_utc():
    m = TelemetryIn(device_id="D1", timestamp="2026-10-01T07:11:11+00:00")
    assert m.timestamp == datetime(2026, 10, 1, 7, 11, 11)
    assert m.timestamp.tzinfo is None


def test_offset_timestamp_is_converted_to_utc():
    m = TelemetryIn(device_id="D1", timestamp="2026-10-01T12:41:11+05:30")
    assert m.timestamp == datetime(2026, 10, 1, 7, 11, 11)


def test_temperature_out_of_range_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(device_id="D1", temperature=9999)


def test_battery_over_100_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(device_id="D1", battery=101)


def test_bad_device_id_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(device_id="bad id!")


def test_missing_device_id_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(temperature=30)


def test_nan_temperature_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(device_id="D1", temperature=float("nan"))