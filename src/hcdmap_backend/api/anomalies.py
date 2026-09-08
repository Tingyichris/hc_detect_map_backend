from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Anomaly
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"], dependencies=[Depends(require_user)])


@router.get("")
def list_anomalies(status: str = "open", db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(Anomaly)
        .where(Anomaly.store_id == settings.store_id, Anomaly.status == status)
        .order_by(Anomaly.ts.desc())
        .limit(200)
    ).all()
    return [
        {"id": a.id, "kind": a.kind, "camera_id": a.camera_id, "detail": a.detail,
         "ts": a.ts, "severity": a.severity, "status": a.status}
        for a in rows
    ]


@router.post("/{anomaly_id}/ack")
def ack(anomaly_id: int, db: Session = Depends(get_db)) -> dict:
    row = db.get(Anomaly, anomaly_id)
    if row is None:
        raise HTTPException(404, "no such anomaly")
    row.status = "acknowledged"
    db.flush()
    return {"id": row.id, "status": row.status}
