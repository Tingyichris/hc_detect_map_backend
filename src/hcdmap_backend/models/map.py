from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class MapVersion(Base, StoreScoped):
    """Immutable versioned map config from the editor. `active` marks the live one."""

    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    version: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=False)
    floorplan_image_id: Mapped[str] = mapped_column(String(64))
    # Full document as defined in shared/map-schema.md (path_px, cameras, ...).
    doc: Mapped[dict] = mapped_column(JSON)
    author: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (UniqueConstraint("store_id", "version", name="uq_map_store_version"),)


class Floorplan(Base, StoreScoped):
    __tablename__ = "floorplans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)   # fp_xxxx
    filename: Mapped[str] = mapped_column(String(255))
    width_px: Mapped[int] = mapped_column(Integer)
    height_px: Mapped[int] = mapped_column(Integer)
    path: Mapped[str] = mapped_column(String(512))                  # on-disk location
