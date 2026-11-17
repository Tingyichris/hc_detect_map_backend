from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera
from ..settings import settings
from ..config_signal.publisher import publish_camera_aoi
from .deps import get_db, require_user

router = APIRouter(prefix="/api/cameras", tags=["cameras"], dependencies=[Depends(require_user)])


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
    return [
        {"id": c.id, "source_id": c.id, "pi_id": c.pi_id,
         "camera_id": c.local_camera_id or c.id,
         "role": c.role, "table_id": c.table_id, "state": c.state,
         "last_reason": c.last_reason, "last_seen_at": c.last_seen_at,
         "snapshot_url": f"/api/cameras/snapshot?source_id={c.id}" if c.snapshot_path else None,
         "has_aoi": bool(c.aoi_json),
         "occluded_seconds_today": c.occluded_seconds_today,
         "dropped_msgs_today": c.dropped_msgs_today}
        for c in rows
    ]


@router.get("/snapshot")
def camera_snapshot(source_id: str = Query(...), db: Session = Depends(get_db)):
    row = db.get(Camera, source_id)
    if row is None or not row.snapshot_path or not Path(row.snapshot_path).is_file():
        raise HTTPException(404, "camera snapshot unavailable")
    return FileResponse(row.snapshot_path, media_type="image/jpeg")


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
