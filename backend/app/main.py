from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import alerts, analytics, auth, devices, health, telemetry, thresholds
from backend.app.config import get_settings
from backend.app.logging_config import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(alerts.router)
app.include_router(thresholds.router)
app.include_router(telemetry.router)
app.include_router(analytics.router)

# Serve the dashboard files (frontend/css, frontend/js) and the main page.
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(FRONTEND_DIR / "index.html")