from __future__ import annotations

from sqlalchemy import Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class PlateClass(Base, StoreScoped):
    """class string (from the Pi detector) -> price + display colour. Bills are derived from this."""

    __tablename__ = "plate_classes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32))          # "red", "gold", ...
    price: Mapped[float] = mapped_column(Float)
    color: Mapped[str] = mapped_column(String(16), default="#888888")
    label: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (UniqueConstraint("store_id", "name", name="uq_class_store_name"),)
