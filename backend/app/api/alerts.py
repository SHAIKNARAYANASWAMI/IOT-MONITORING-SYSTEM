from typing import Literal
from backend.app.api.auth import require_auth

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.logging_config import get_logger
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.schemas.api_schemas import AlertOut

logger = get_logger("api.alerts")
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: Literal["OPEN", "ACKNOWLEDGED", "RESOLVED"] | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return AlertRepository(db).list_alerts(status=status, limit=limit)


@router.put("/{alert_id}/acknowledge", response_model=AlertOut, dependencies=[Depends(require_auth)])
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = AlertRepository(db).acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    logger.info("Alert %s acknowledged via API", alert_id)
    return alert
@router.put("/{alert_id}/resolve", response_model=AlertOut, dependencies=[Depends(require_auth)])
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = AlertRepository(db).resolve(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    logger.info("Alert %s resolved via API", alert_id)
    return alert