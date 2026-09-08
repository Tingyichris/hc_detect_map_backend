"""server -> backend result feed. Every handler is idempotent: upsert on `event_id`."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Anomaly, Camera, PickupEvent
from ..schemas import AnomalyIn, CameraStatusIn, CheckpointCrossingsIn, PickupIn
from ..sessions.lifecycle import attach_to_open_session
from .deps import get_db, require_service_token

router = APIRouter(prefix="/api/ingest", tags=["ingest"], dependencies=[Depends(require_service_token)])


@router.post("/pickups")
def ingest_pickup(body: PickupIn, db: Session = Depends(get_db)) -> dict:
    existing = db.scalar(select(PickupEvent).where(PickupEvent.event_id == body.event_id))
    if existing:
        return {"status": "duplicate", "id": existing.id}

    row = PickupEvent(
        event_id=body.event_id,
        store_id=body.store_id,
        gid=body.gid,
        table_id=body.table_id,
        camera_id=body.camera_id,
        plate_class=body.plate_class,
        ts=body.ts,
        confidence=body.confidence,
        method=body.method,
        segment_upstream=body.segment[0],
        segment_downstream=body.segment[1],
        kitchen_removal=body.kitchen_removal,
        integrity=body.integrity,
        review_status="pending" if (body.confidence < 0.6 or body.table_id is None) else None,
    )
    if not body.kitchen_removal and body.table_id:
        row.session_id = attach_to_open_session(db, body.store_id, body.table_id, body.ts)
    db.add(row)
    db.flush()
    return {"status": "ok", "id": row.id, "review": row.review_status}


@router.post("/anomalies")
def ingest_anomaly(body: AnomalyIn, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(Anomaly).where(Anomaly.event_id == body.event_id)):
        return {"status": "duplicate"}
    db.add(Anomaly(**body.model_dump()))
    return {"status": "ok"}


@router.post("/camera-status")
def ingest_camera_status(body: CameraStatusIn, db: Session = Depends(get_db)) -> dict:
    cam = db.get(Camera, body.camera_id)
    if cam is None:
        cam = Camera(id=body.camera_id, store_id=body.store_id)
        db.add(cam)
    cam.state = body.state
    cam.last_reason = body.reason
    # last_seen_at / rollups: TODO update from ts
    return {"status": "ok"}


@router.post("/checkpoint-crossings")
def ingest_crossings(body: CheckpointCrossingsIn) -> dict:
    # Optional audit stream. TODO: persist to a rolling table or drop if not needed.
    return {"status": "ok", "count": len(body.crossings)}
