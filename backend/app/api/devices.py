from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.logging_config import get_logger
from backend.app.repositories.device_repository import DeviceRepository
from backend.app.repositories.reading_repository import ReadingRepository
from backend.app.schemas.api_schemas import DeviceCreate, DeviceOut, ReadingOut

logger = get_logger("api.devices")
router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("", response_model=DeviceOut, status_code=201)
def register_device(body: DeviceCreate, db: Session = Depends(get_db)):
    repo = DeviceRepository(db)
    if repo.get_by_device_id(body.device_id) is not None:
        raise HTTPException(status_code=409, detail=f"Device {body.device_id} already exists")
    device = repo.add(body.device_id, body.name, body.location)
    logger.info("Device registered via API: %s", body.device_id)
    return device


@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    return DeviceRepository(db).list_all()


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: str, db: Session = Depends(get_db)):
    device = DeviceRepository(db).get_by_device_id(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


@router.get("/{device_id}/readings", response_model=list[ReadingOut])
def get_readings(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    if DeviceRepository(db).get_by_device_id(device_id) is None:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return ReadingRepository(db).list_for_device(device_id, limit=limit)