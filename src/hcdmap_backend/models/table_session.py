from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class TableSession(Base, StoreScoped):
    """A seat-to-clear dining session at one table. Pickups accumulate against the open one."""

    __tablename__ = "table_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    table_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(16), default="open")     # open | closed
    opened_at: Mapped[datetime] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    close_reason: Mapped[str | None] = mapped_column(String(32))        # pos | manual | auto

    # Frozen at close: {class: count}, total, bill. Live sessions compute these on the fly.
    counts_by_class: Mapped[dict | None] = mapped_column(JSON, default=None)
    total_plates: Mapped[int | None] = mapped_column(default=None)
    bill: Mapped[float | None] = mapped_column(Float, default=None)

    # POS / manual reconciliation
    reconciled_count: Mapped[int | None] = mapped_column(default=None)
    reconciled_bill: Mapped[float | None] = mapped_column(Float, default=None)
    discrepancy: Mapped[int | None] = mapped_column(default=None)

    integrity: Mapped[str] = mapped_column(String(16), default="ok")    # degraded if a camera was down mid-session
