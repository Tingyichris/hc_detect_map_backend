"""Table-session lifecycle + bills + POS reconcile. STUB bodies; shapes match docs/api-contract.md."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PickupEvent, PlateClass, TableSession
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"], dependencies=[Depends(require_user)])


def _bill(db: Session, counts: dict[str, int]) -> float:
    prices = {
        p.name: p.price
        for p in db.scalars(select(PlateClass).where(PlateClass.store_id == settings.store_id))
    }
    return round(sum(prices.get(k, 0.0) * n for k, n in counts.items()), 2)


@router.get("")
def list_sessions(status: str = "open", db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(TableSession).where(
            TableSession.store_id == settings.store_id, TableSession.status == status
        )
    ).all()
    return [{"id": r.id, "table_id": r.table_id, "status": r.status, "opened_at": r.opened_at} for r in rows]


@router.post("/{table_id}/open")
def open_session(table_id: str, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(
        select(TableSession).where(
            TableSession.store_id == settings.store_id,
            TableSession.table_id == table_id,
            TableSession.status == "open",
        )
    )
    if existing:
        return {"id": existing.id, "status": "already_open"}
    row = TableSession(
        store_id=settings.store_id, table_id=table_id, status="open", opened_at=datetime.utcnow()
    )
    db.add(row)
    db.flush()
    return {"id": row.id, "status": "open"}


@router.post("/{table_id}/close")
def close_session(table_id: str, reason: str = "manual", db: Session = Depends(get_db)) -> dict:
    row = db.scalar(
        select(TableSession).where(
            TableSession.store_id == settings.store_id,
            TableSession.table_id == table_id,
            TableSession.status == "open",
        )
    )
    if row is None:
        raise HTTPException(404, "no open session for that table")
    pickups = db.scalars(
        select(PickupEvent).where(
            PickupEvent.session_id == row.id, PickupEvent.kitchen_removal.is_(False)
        )
    ).all()
    counts: dict[str, int] = {}
    for p in pickups:
        counts[p.plate_class] = counts.get(p.plate_class, 0) + 1
    # TODO: apply corrections rows on top of counts
    row.counts_by_class = counts
    row.total_plates = sum(counts.values())
    row.bill = _bill(db, counts)
    row.status = "closed"
    row.close_reason = reason
    row.closed_at = datetime.utcnow()
    if any(p.integrity != "ok" for p in pickups):
        row.integrity = "degraded"
    db.flush()
    return {"id": row.id, "total_plates": row.total_plates, "bill": row.bill, "integrity": row.integrity}


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(TableSession, session_id)
    if row is None:
        raise HTTPException(404, "no such session")
    pickups = db.scalars(select(PickupEvent).where(PickupEvent.session_id == session_id)).all()
    return {
        "id": row.id,
        "table_id": row.table_id,
        "status": row.status,
        "opened_at": row.opened_at,
        "closed_at": row.closed_at,
        "bill": row.bill,
        "integrity": row.integrity,
        "pickups": [
            {"gid": p.gid, "class": p.plate_class, "ts": p.ts, "confidence": p.confidence,
             "method": p.method, "camera_id": p.camera_id, "review_status": p.review_status}
            for p in pickups
        ],
    }


@router.post("/{session_id}/reconcile")
def reconcile(session_id: int, reconciled_count: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(TableSession, session_id)
    if row is None:
        raise HTTPException(404, "no such session")
    row.reconciled_count = reconciled_count
    row.discrepancy = (row.total_plates or 0) - reconciled_count
    db.flush()
    return {"id": row.id, "discrepancy": row.discrepancy}
