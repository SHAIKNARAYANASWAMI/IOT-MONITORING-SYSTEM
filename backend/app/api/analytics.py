from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.schemas.api_schemas import AlertOut
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/devices/{device_id}/smoothed-temperature")
def smoothed_temperature(
    device_id: str,
    window: int = Query(default=5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if DeviceRepository(db).get_by_device_id(device_id) is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return AnalyticsService(db).smoothed_temperature(device_id, window)


@router.get("/urgent-alerts", response_model=list[AlertOut])
def urgent_alerts(count: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    return AnalyticsService(db).urgent_alerts(count)


@router.get("/alert-report", response_model=list[AlertOut])
def alert_report(db: Session = Depends(get_db)):
    return AnalyticsService(db).alert_report()