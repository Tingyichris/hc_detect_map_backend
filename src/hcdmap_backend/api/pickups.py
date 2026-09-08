from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PickupEvent
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/pickups", tags=["pickups"], dependencies=[Depends(require_user)])


@router.get("")
def list_pickups(
    session_id: int | None = None,
    table_id: str | None = None,
    since: float | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    q = select(PickupEvent).where(PickupEvent.store_id == settings.store_id)
    if session_id is not None:
        q = q.where(PickupEvent.session_id == session_id)
    if table_id is not None:
        q = q.where(PickupEvent.table_id == table_id)
    if since is not None:
        q = q.where(PickupEvent.ts >= since)
    rows = db.scalars(q.order_by(PickupEvent.ts.desc()).limit(500)).all()
    return [
        {"id": r.id, "gid": r.gid, "table_id": r.table_id, "class": r.plate_class, "ts": r.ts,
         "confidence": r.confidence, "method": r.method, "integrity": r.integrity,
         "review_status": r.review_status}
        for r in rows
    ]
