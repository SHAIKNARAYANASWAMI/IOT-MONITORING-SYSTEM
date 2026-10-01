from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.session import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="")
    location: Mapped[str] = mapped_column(String(100), default="")
    status: Mapped[str] = mapped_column(String(20), default="OFFLINE")
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (Index("ix_readings_device_time", "device_id", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    humidity: Mapped[float | None] = mapped_column(Float)
    voltage: Mapped[float | None] = mapped_column(Float)
    current: Mapped[float | None] = mapped_column(Float)
    pressure: Mapped[float | None] = mapped_column(Float)
    battery: Mapped[int | None] = mapped_column(Integer)

    device = relationship("Device", back_populates="readings")


class Threshold(Base):
    __tablename__ = "thresholds"
    __table_args__ = (UniqueConstraint("device_id", "metric", name="uq_threshold_device_metric"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # NULL device_id means a global default threshold for all devices
    device_id: Mapped[str | None] = mapped_column(ForeignKey("devices.device_id"), nullable=True)
    metric: Mapped[str] = mapped_column(String(30), nullable=False)
    min_value: Mapped[float | None] = mapped_column(Float)
    max_value: Mapped[float | None] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(10), default="WARNING")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_status_severity", "status", "severity"),
        CheckConstraint("severity IN ('INFO','WARNING','CRITICAL')", name="ck_alert_severity"),
        CheckConstraint("status IN ('OPEN','ACKNOWLEDGED','RESOLVED')", name="ck_alert_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.device_id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    actual_value: Mapped[float | None] = mapped_column(Float)
    threshold_value: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(15), default="OPEN", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    device = relationship("Device", back_populates="alerts")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)
    component: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    device_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)