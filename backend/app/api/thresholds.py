from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.api.auth import require_auth

from backend.app.database.session import get_db
from backend.app.logging_config import get_logger
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.threshold_repository import ThresholdRepository
from backend.app.schemas.api_schemas import ThresholdIn, ThresholdOut

logger = get_logger("api.thresholds")
router = APIRouter(prefix="/thresholds", tags=["thresholds"])


@router.post("", response_model=ThresholdOut, dependencies=[Depends(require_auth)])
def set_threshold(body: ThresholdIn, db: Session = Depends(get_db)):
    if body.min_value is None and body.max_value is None:
        raise HTTPException(status_code=422, detail="Provide min_value, max_value, or both")
    if (
        body.min_value is not None
        and body.max_value is not None
        and body.min_value >= body.max_value
    ):
        raise HTTPException(status_code=422, detail="min_value must be less than max_value")
    if body.device_id is not None and DeviceRepository(db).get_by_device_id(body.device_id) is None:
        raise HTTPException(status_code=404, detail=f"Device {body.device_id} not found")

    threshold = ThresholdRepository(db).upsert(
        body.metric, body.min_value, body.max_value, body.severity, body.device_id
    )
    logger.info("Threshold set: %s device=%s", body.metric, body.device_id or "GLOBAL")
    return threshold


@router.get("", response_model=list[ThresholdOut])
def list_thresholds(db: Session = Depends(get_db)):
    return ThresholdRepository(db).list_all()