"""Request models for the server -> backend result feed. Mirrors docs/api-contract.md section 1."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PickupIn(BaseModel):
    event_id: str
    store_id: str
    gid: str
    table_id: str | None = None
    camera_id: str
    plate_class: str = Field(alias="class")
    ts: float
    confidence: float = Field(ge=0.0, le=1.0)
    method: Literal["conservation", "offbelt_confirmed", "occluded_suspect"]
    segment: tuple[str, str]
    kitchen_removal: bool = False
    integrity: Literal["ok", "estimated", "degraded"] = "ok"

    model_config = {"populate_by_name": True}


class AnomalyIn(BaseModel):
    event_id: str
    store_id: str
    kind: Literal[
        "camera_occluded",
        "conservation_mismatch",
        "low_confidence_pickup",
        "clock_skew",
        "bad_payload",
        "belt_stopped",
    ]
    camera_id: str | None = None
    detail: str = ""
    ts: float
    severity: Literal["info", "warn", "critical"] = "warn"


class CameraStatusIn(BaseModel):
    event_id: str
    store_id: str
    camera_id: str
    state: Literal["online", "degraded", "offline"]
    reason: str = "ok"
    ts: float


class _Crossing(BaseModel):
    camera_id: str
    gid: str
    plate_class: str = Field(alias="class")
    ts: float

    model_config = {"populate_by_name": True}


class CheckpointCrossingsIn(BaseModel):
    event_id: str
    store_id: str
    crossings: list[_Crossing]
