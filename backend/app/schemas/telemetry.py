from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class TelemetryIn(BaseModel):
    """Validates one incoming sensor message. Anything out of range is rejected."""

    device_id: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    timestamp: datetime | None = None
    temperature: float | None = Field(default=None, ge=-50, le=150)
    humidity: float | None = Field(default=None, ge=0, le=100)
    voltage: float | None = Field(default=None, ge=0, le=500)
    current: float | None = Field(default=None, ge=0, le=100)
    pressure: float | None = Field(default=None, ge=50, le=200)
    battery: int | None = Field(default=None, ge=0, le=100)
    status: str = "ONLINE"

    @field_validator("timestamp")
    @classmethod
    def to_naive_utc(cls, value):
        """The database stores naive UTC datetimes, so convert here once."""
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value