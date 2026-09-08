from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class Camera(Base, StoreScoped):
    """Camera registry + rolling health/reliability stats (updated from the ingest feed)."""

    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    role: Mapped[str] = mapped_column(String(16), default="table")   # table | source
    table_id: Mapped[str | None] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(16), default="offline")   # online | degraded | offline
    last_reason: Mapped[str] = mapped_column(String(32), default="lwt")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # reliability rollups
    occluded_seconds_today: Mapped[float] = mapped_column(Float, default=0.0)
    dropped_msgs_today: Mapped[int] = mapped_column(Integer, default=0)
