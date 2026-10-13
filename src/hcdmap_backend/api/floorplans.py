from __future__ import annotations

import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..models import Floorplan
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/floorplans", tags=["floorplans"])

ALLOWED_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}


def floorplan_root() -> Path:
    root = Path(settings.floorplan_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root


@router.post("")
async def upload_floorplan(
    file: UploadFile = File(...),
    width_px: int = Form(0),
    height_px: int = Form(0),
    _user: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    ext = ALLOWED_TYPES.get(content_type)
    if not ext:
        raise HTTPException(415, "floorplan must be png, jpeg, webp, or gif")

    fid = f"fp_{uuid4().hex[:12]}"
    dest = floorplan_root() / f"{fid}{ext}"
    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > 20 * 1024 * 1024:
                dest.unlink(missing_ok=True)
                raise HTTPException(413, "floorplan image is too large")
            out.write(chunk)

    row = Floorplan(
        store_id=settings.store_id,
        id=fid,
        filename=file.filename or dest.name,
        width_px=max(0, width_px),
        height_px=max(0, height_px),
        path=str(dest),
    )
    db.add(row)
    return {
        "id": fid,
        "url": f"/api/floorplans/{fid}/file",
        "filename": row.filename,
        "width_px": row.width_px,
        "height_px": row.height_px,
    }


@router.get("/{fid}")
def get_floorplan(
    fid: str,
    _user: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Floorplan, fid)
    if row is None or row.store_id != settings.store_id:
        raise HTTPException(404, "no such floorplan")
    return {
        "id": row.id,
        "filename": row.filename,
        "width_px": row.width_px,
        "height_px": row.height_px,
        "url": f"/api/floorplans/{row.id}/file",
    }


@router.get("/{fid}/file")
def get_floorplan_file(fid: str, db: Session = Depends(get_db)) -> FileResponse:
    row = db.get(Floorplan, fid)
    if row is None or row.store_id != settings.store_id:
        raise HTTPException(404, "no such floorplan")
    path = Path(row.path)
    if not path.exists():
        raise HTTPException(404, "floorplan file missing")
    return FileResponse(path, filename=row.filename)
