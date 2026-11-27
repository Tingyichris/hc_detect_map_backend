"""Pipeline health: broker reachable, fusion server heartbeat, per-Pi last-seen, processing lag."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera
from ..settings import settings
from .cameras import camera_payload
from .deps import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    cams = db.scalars(select(Camera).where(Camera.store_id == settings.store_id)).all()
    now = datetime.now(UTC).replace(tzinfo=None)
    registered = [payload for camera in cams if (payload := camera_payload(camera, now))]
    return {
        "store_id": settings.store_id,
        # TODO: server heartbeat (fusion server should POST a heartbeat or expose /healthz we poll)
        "server": {"status": "unknown"},
        "broker": {"status": "unknown"},   # TODO: cheap connect check to settings.mqtt_host
        "cameras": [
            {
                "id": camera["id"],
                "state": camera["state"],
                "last_seen_age_s": camera["last_seen_age_s"],
            }
            for camera in registered
        ],
    }
