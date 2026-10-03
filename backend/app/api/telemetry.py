from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from backend.app.logging_config import get_logger
from backend.app.schemas.telemetry import TelemetryIn
from backend.app.services.ingestion_service import IngestionService

logger = get_logger("api.telemetry")
router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# Reuses the same validation + save + alert logic as MQTT messages.
# We call process() directly (no queue/thread) so the caller gets an immediate result.
_service = IngestionService()


@router.post("", status_code=201)
def post_telemetry(payload: dict):
    try:
        TelemetryIn(**payload)
    except ValidationError as exc:
        err = exc.errors()[0]
        field = ".".join(str(p) for p in err["loc"])
        raise HTTPException(status_code=422, detail=f"Invalid {field}: {err['msg']}")

    if not _service.process(payload):
        raise HTTPException(status_code=500, detail="Failed to store telemetry")
    logger.info("Telemetry received via HTTP from %s", payload.get("device_id"))
    return {"status": "stored", "device_id": payload.get("device_id")}