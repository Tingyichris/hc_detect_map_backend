from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PlateClass
from ..settings import settings
from .deps import get_db, require_user

router = APIRouter(prefix="/api/plate-classes", tags=["plate-classes"])


class PlateClassIn(BaseModel):
    name: str
    price: float
    color: str = "#888888"
    label: str | None = None


@router.get("")
def list_classes(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(PlateClass).where(PlateClass.store_id == settings.store_id)).all()
    return [{"name": r.name, "price": r.price, "color": r.color, "label": r.label} for r in rows]


@router.put("")
def replace_classes(
    items: list[PlateClassIn], _: dict = Depends(require_user), db: Session = Depends(get_db)
) -> dict:
    db.query(PlateClass).filter(PlateClass.store_id == settings.store_id).delete()
    for it in items:
        db.add(PlateClass(store_id=settings.store_id, **it.model_dump()))
    db.flush()
    return {"count": len(items)}
