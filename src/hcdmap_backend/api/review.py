"""Review queue for low-confidence / unattributed pickups."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PickupEvent
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/review", tags=["review"], dependencies=[Depends(require_user)])


@router.get("")
def queue(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(PickupEvent).where(
            PickupEvent.store_id == settings.store_id,
            PickupEvent.review_status == "pending",
        ).order_by(PickupEvent.ts)
    ).all()
    return [
        {"id": r.id, "gid": r.gid, "suggested_table": r.table_id, "class": r.plate_class,
         "ts": r.ts, "confidence": r.confidence, "method": r.method,
         "segment": [r.segment_upstream, r.segment_downstream], "camera_id": r.camera_id}
        for r in rows
    ]


@router.post("/{pickup_id}/assign")
def assign(pickup_id: int, table_id: str = Body(embed=True), db: Session = Depends(get_db)) -> dict:
    row = db.get(PickupEvent, pickup_id)
    if row is None:
        raise HTTPException(404, "no such pickup")
    row.table_id = table_id
    row.review_status = "assigned"
    # TODO: re-attach to that table's open session
    db.flush()
    return {"id": row.id, "table_id": table_id}


@router.post("/{pickup_id}/dismiss")
def dismiss(pickup_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(PickupEvent, pickup_id)
    if row is None:
        raise HTTPException(404, "no such pickup")
    row.review_status = "dismissed"
    row.session_id = None
    db.flush()
    return {"id": row.id, "status": "dismissed"}
