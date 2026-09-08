from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/cameras", tags=["cameras"], dependencies=[Depends(require_user)])


@router.get("")
def list_cameras(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Camera).where(Camera.store_id == settings.store_id)).all()
    return [
        {"id": c.id, "role": c.role, "table_id": c.table_id, "state": c.state,
         "last_reason": c.last_reason, "last_seen_at": c.last_seen_at,
         "occluded_seconds_today": c.occluded_seconds_today,
         "dropped_msgs_today": c.dropped_msgs_today}
        for c in rows
    ]
