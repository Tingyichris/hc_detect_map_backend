from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera
from ..settings import settings
from ..config_signal.publisher import publish_camera_aoi, publish_camera_screenshot_request
from .deps import get_db, require_user

router = APIRouter(prefix="/api/cameras", tags=["cameras"], dependencies=[Depends(require_user)])


def camera_payload(camera: Camera, now: datetime | None = None) -> dict | None:
    """Return MQTT-registered cameras using their last reported session state."""
    if not camera.pi_id or not camera.local_camera_id or camera.last_seen_at is None:
        return None
    current = now or datetime.now(UTC).replace(tzinfo=None)
    age_s = max(0.0, (current - camera.last_seen_at).total_seconds())
    state = camera.state
    snapshot_available = bool(camera.snapshot_path and Path(camera.snapshot_path).is_file())
    return {
        "id": camera.id,
        "source_id": camera.id,
        "pi_id": camera.pi_id,
        "camera_id": camera.local_camera_id,
        "role": camera.role,
        "table_id": camera.table_id,
        "state": state,
        "reported_state": camera.state,
        "last_reason": camera.last_reason,
        "last_seen_at": camera.last_seen_at,
        "last_seen_age_s": round(age_s, 1),
        "snapshot_updated_at": camera.snapshot_updated_at,
        "snapshot_url": (
            f"/api/cameras/snapshot?source_id={camera.id}" if snapshot_available else None
        ),
        "has_aoi": bool(camera.aoi_json),
        "occluded_seconds_today": camera.occluded_seconds_today,
        "dropped_msgs_today": camera.dropped_msgs_today,
    }


class AoiBody(BaseModel):
    points: list[list[float]]

    @field_validator("points")
    @classmethod
    def validate_points(cls, value):
        if len(value) != 4 or any(len(point) != 2 for point in value):
            raise ValueError("AOI requires exactly four [x,y] points")
        if any(not 0 <= number <= 1 for point in value for number in point):
            raise ValueError("AOI coordinates must be normalized to 0..1")
        return value


@router.get("")
def list_cameras(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(Camera).where(Camera.store_id == settings.store_id)).all()
    now = datetime.now(UTC).replace(tzinfo=None)
    payloads = (camera_payload(camera, now) for camera in rows)
    return [payload for payload in payloads if payload is not None]


@router.get("/snapshot")
def camera_snapshot(source_id: str = Query(...), db: Session = Depends(get_db)):
    row = db.get(Camera, source_id)
    if row is None or not row.snapshot_path or not Path(row.snapshot_path).is_file():
        raise HTTPException(404, "camera snapshot unavailable")
    return FileResponse(
        row.snapshot_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@router.post("/snapshot/request")
def request_camera_snapshot(source_id: str = Query(...), db: Session = Depends(get_db)) -> dict:
    row = db.get(Camera, source_id)
    if row is None or not row.pi_id or not row.local_camera_id:
        raise HTTPException(404, "camera not registered")
    request_id = str(uuid.uuid4())
    publish_camera_screenshot_request(row.pi_id, row.local_camera_id, request_id)
    return {"status": "requested", "source_id": source_id, "request_id": request_id}


@router.get("/aoi")
def get_aoi(source_id: str = Query(...), db: Session = Depends(get_db)) -> dict:
    row = db.get(Camera, source_id)
    if row is None:
        raise HTTPException(404, "camera not registered")
    return {"source_id": source_id, "points": json.loads(row.aoi_json) if row.aoi_json else []}


@router.put("/aoi")
def put_aoi(body: AoiBody, source_id: str = Query(...), db: Session = Depends(get_db)) -> dict:
    row = db.get(Camera, source_id)
    if row is None or not row.pi_id or not row.local_camera_id:
        raise HTTPException(404, "camera not registered")
    row.aoi_json = json.dumps(body.points, separators=(",", ":"))
    publish_camera_aoi(row.pi_id, row.local_camera_id, body.points)
    return {"status": "ok", "source_id": source_id, "points": body.points}
