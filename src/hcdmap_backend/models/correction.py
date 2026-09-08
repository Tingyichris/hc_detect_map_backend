from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class Correction(Base, StoreScoped):
    """Staff manual adjustment to a table's tally. Never edits a pickup_events row — it is an
    additive audit record that the derived tally applies on top."""

    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int | None] = mapped_column(Integer, index=True)
    table_id: Mapped[str] = mapped_column(String(32), index=True)
    delta: Mapped[int] = mapped_column(Integer)                # +1 add a plate, -1 remove
    plate_class: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    user: Mapped[str] = mapped_column(String(64))
    ref_pickup_event_id: Mapped[str | None] = mapped_column(String(64))   # if correcting a specific pickup
