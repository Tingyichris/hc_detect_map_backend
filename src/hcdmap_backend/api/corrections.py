from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models import Correction
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/corrections", tags=["corrections"])


class CorrectionIn(BaseModel):
    table_id: str
    delta: int          # +1 add a plate, -1 remove
    plate_class: str
    reason: str
    session_id: int | None = None
    ref_pickup_event_id: str | None = None


@router.post("")
def create_correction(
    body: CorrectionIn, user: dict = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    row = Correction(
        store_id=settings.store_id,
        session_id=body.session_id,
        table_id=body.table_id,
        delta=body.delta,
        plate_class=body.plate_class,
        reason=body.reason,
        user=user["sub"],
        ref_pickup_event_id=body.ref_pickup_event_id,
    )
    db.add(row)
    db.flush()
    return {"id": row.id}
