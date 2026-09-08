"""Versioned map CRUD. Saving a new version publishes the sushi/<store>/config/map signal."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config_signal.publisher import publish_map_signal
from ..models import MapVersion
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/maps", tags=["maps"])


@router.get("")
def list_maps(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(MapVersion).where(MapVersion.store_id == settings.store_id).order_by(MapVersion.version.desc())
    ).all()
    return [{"version": r.version, "active": r.active, "author": r.author} for r in rows]


@router.get("/current")
def current_map(db: Session = Depends(get_db)) -> dict:
    row = db.scalar(
        select(MapVersion).where(
            MapVersion.store_id == settings.store_id, MapVersion.active.is_(True)
        )
    )
    if row is None:
        raise HTTPException(404, "no active map — create one in the editor")
    return {"version": row.version, "store_id": row.store_id, **row.doc}


@router.get("/{version}")
def get_map(version: int, db: Session = Depends(get_db)) -> dict:
    row = db.scalar(
        select(MapVersion).where(
            MapVersion.store_id == settings.store_id, MapVersion.version == version
        )
    )
    if row is None:
        raise HTTPException(404, "no such version")
    return {"version": row.version, "store_id": row.store_id, "active": row.active, **row.doc}


@router.post("")
def save_map(doc: dict, user: dict = Depends(require_user), db: Session = Depends(get_db)) -> dict:
    last = db.scalar(
        select(MapVersion.version)
        .where(MapVersion.store_id == settings.store_id)
        .order_by(MapVersion.version.desc())
    )
    version = (last or 0) + 1
    row = MapVersion(
        store_id=settings.store_id,
        version=version,
        active=False,
        floorplan_image_id=doc.get("floorplan", {}).get("image_id", ""),
        doc=doc,
        author=user["sub"],
    )
    db.add(row)
    db.flush()
    return {"version": version, "active": False}


@router.post("/{version}/activate")
def activate_map(version: int, db: Session = Depends(get_db), user: dict = Depends(require_user)) -> dict:
    rows = db.scalars(
        select(MapVersion).where(MapVersion.store_id == settings.store_id)
    ).all()
    target = next((r for r in rows if r.version == version), None)
    if target is None:
        raise HTTPException(404, "no such version")
    for r in rows:
        r.active = r.version == version
    db.flush()
    publish_map_signal(settings.store_id, version)
    return {"version": version, "active": True}
