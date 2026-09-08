"""Pipeline health: broker reachable, fusion server heartbeat, per-Pi last-seen, processing lag."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera
from ..settings import settings
from .deps import get_db

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    cams = db.scalars(select(Camera).where(Camera.store_id == settings.store_id)).all()
    now = time.time()
    return {
        "store_id": settings.store_id,
        # TODO: server heartbeat (fusion server should POST a heartbeat or expose /healthz we poll)
        "server": {"status": "unknown"},
        "broker": {"status": "unknown"},   # TODO: cheap connect check to settings.mqtt_host
        "cameras": [
            {
                "id": c.id,
                "state": c.state,
                "last_seen_age_s": (now - c.last_seen_at.timestamp()) if c.last_seen_at else None,
            }
            for c in cams
        ],
    }
