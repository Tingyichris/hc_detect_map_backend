from __future__ import annotations

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, StoreScoped


class Anomaly(Base, StoreScoped):
    """Pipeline / integrity events surfaced to staff. Written by the ingest feed."""

    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True)

    kind: Mapped[str] = mapped_column(String(32))
    # camera_occluded | conservation_mismatch | low_confidence_pickup | clock_skew | bad_payload | belt_stopped
    camera_id: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")
    ts: Mapped[float] = mapped_column(Float, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="warn")   # info | warn | critical
    status: Mapped[str] = mapped_column(String(16), default="open")     # open | acknowledged | closed
