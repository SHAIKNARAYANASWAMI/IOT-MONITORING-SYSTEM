from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.models import Alert, Device

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    """Quick system summary: is the API up, is the DB reachable, how many devices/alerts."""
    total = db.execute(select(func.count()).select_from(Device)).scalar_one()
    online = db.execute(
        select(func.count()).select_from(Device).where(Device.status == "ONLINE")
    ).scalar_one()
    active_alerts = db.execute(
        select(func.count()).select_from(Alert).where(Alert.status != "RESOLVED")
    ).scalar_one()
    return {
        "status": "ok",
        "database": "connected",
        "devices_total": total,
        "devices_online": online,
        "active_alerts": active_alerts,
    }