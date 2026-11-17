"""server -> backend result feed. Every handler is idempotent: upsert on `event_id`."""
from __future__ import annotations

from datetime import UTC, datetime

import hashlib
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Anomaly, Camera, PickupEvent
from ..schemas import AnomalyIn, CameraStatusIn, CheckpointCrossingsIn, PickupIn
from ..settings import settings
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
    if "/" in body.camera_id:
        cam.pi_id, cam.local_camera_id = body.camera_id.split("/", 1)
    cam.state = body.state
    cam.last_reason = body.reason
    cam.last_seen_at = datetime.fromtimestamp(body.ts, UTC).replace(tzinfo=None)
    return {"status": "ok"}


@router.post("/checkpoint-crossings")
def ingest_crossings(body: CheckpointCrossingsIn) -> dict:
    # Optional audit stream. TODO: persist to a rolling table or drop if not needed.
    return {"status": "ok", "count": len(body.crossings)}


@router.post("/camera-snapshot")
async def ingest_camera_snapshot(
    request: Request, source_id: str = Query(...), db: Session = Depends(get_db)
) -> dict:
    payload = await request.body()
    if not payload or len(payload) > 5 * 1024 * 1024:
        raise HTTPException(413, "snapshot must be a JPEG up to 5 MB")
    row = db.get(Camera, source_id)
    if row is None:
        pi_id, separator, camera_id = source_id.partition("/")
        if not separator:
            raise HTTPException(400, "source_id must be pi_id/camera_id")
        row = Camera(id=source_id, store_id=settings.store_id,
                     pi_id=pi_id, local_camera_id=camera_id)
        db.add(row)
    root = Path(settings.camera_snapshot_dir)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{hashlib.sha256(source_id.encode()).hexdigest()[:24]}.jpg"
    destination.write_bytes(payload)
    row.snapshot_path = str(destination)
    row.snapshot_updated_at = datetime.now(UTC).replace(tzinfo=None)
    return {"status": "ok", "source_id": source_id}
