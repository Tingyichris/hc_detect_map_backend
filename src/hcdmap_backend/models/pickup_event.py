from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class PickupEvent(Base, StoreScoped):
    """One attributed plate leaving the belt. Written ONLY by the idempotent ingest feed."""

    __tablename__ = "pickup_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Deterministic id from the fusion server; retries collide here -> no duplicates.
    event_id: Mapped[str] = mapped_column(String(64), unique=True)

    gid: Mapped[str] = mapped_column(String(32), index=True)
    table_id: Mapped[str | None] = mapped_column(String(32), index=True)
    camera_id: Mapped[str] = mapped_column(String(64))
    plate_class: Mapped[str] = mapped_column(String(32))
    ts: Mapped[float] = mapped_column(Float, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(32))          # conservation | offbelt_confirmed | occluded_suspect
    segment_upstream: Mapped[str] = mapped_column(String(64))
    segment_downstream: Mapped[str] = mapped_column(String(64))
    kitchen_removal: Mapped[bool] = mapped_column(Boolean, default=False)
    integrity: Mapped[str] = mapped_column(String(16), default="ok")   # ok | estimated | degraded

    session_id: Mapped[int | None] = mapped_column(index=True)
    # review workflow: null = accepted, else pending/assigned/dismissed
    review_status: Mapped[str | None] = mapped_column(String(16), default=None)

    __table_args__ = (Index("ix_pickup_store_table_ts", "store_id", "table_id", "ts"),)
