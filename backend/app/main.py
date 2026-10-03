from fastapi import FastAPI

from backend.app.api import alerts, devices, health, telemetry, thresholds
from backend.app.config import get_settings
from backend.app.logging_config import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(health.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(thresholds.router)
app.include_router(telemetry.router)