from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(default="", max_length=100)
    location: str = Field(default="", max_length=100)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    name: str
    location: str
    status: str
    last_seen: datetime | None
    created_at: datetime


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_id: str
    timestamp: datetime
    temperature: float | None
    humidity: float | None
    voltage: float | None
    current: float | None
    pressure: float | None
    battery: int | None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    alert_type: str
    severity: str
    actual_value: float | None
    threshold_value: float | None
    status: str
    created_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None


class ThresholdIn(BaseModel):
    metric: Literal["temperature", "humidity", "voltage", "current", "pressure", "battery"]
    min_value: float | None = None
    max_value: float | None = None
    severity: Literal["INFO", "WARNING", "CRITICAL"] = "WARNING"
    device_id: str | None = None


class ThresholdOut(ThresholdIn):
    model_config = ConfigDict(from_attributes=True)

    id: int