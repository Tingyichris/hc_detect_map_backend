"""Idempotency of the pickup ingest feed, against an in-memory SQLite DB."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from hcdmap_backend.api.deps import get_db
from hcdmap_backend.app import create_app
from hcdmap_backend.models import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def _override_db():
    db = TestSession()
    try:
        yield db
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    app = create_app()
    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


PICKUP = {
    "event_id": "evt-1",
    "store_id": "store-001",
    "gid": "p_000001",
    "table_id": "T02",
    "camera_id": "cam_t02",
    "class": "gold",
    "ts": 1725800000.0,
    "confidence": 0.8,
    "method": "conservation",
    "segment": ["cam_t02", "cam_t03"],
}
HEADERS = {"Authorization": "Bearer dev-service-token"}


def test_same_event_id_posted_twice_creates_one_row(client):
    r1 = client.post("/api/ingest/pickups", json=PICKUP, headers=HEADERS)
    r2 = client.post("/api/ingest/pickups", json=PICKUP, headers=HEADERS)
    assert r1.json()["status"] == "ok"
    assert r2.json()["status"] == "duplicate"
    rows = client.get("/api/pickups", headers={"Authorization": "Bearer u"}).json()
    assert len([x for x in rows if x["gid"] == "p_000001"]) == 1


def test_bad_service_token_rejected(client):
    r = client.post("/api/ingest/pickups", json=PICKUP, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_camera_source_identity_is_split_for_registry_display(client):
    payload = {
        "event_id": "status-1",
        "store_id": "store-001",
        "camera_id": "pi-02/cam-1",
        "state": "online",
        "reason": "ok",
        "ts": 1725800000.0,
    }
    response = client.post("/api/ingest/camera-status", json=payload, headers=HEADERS)
    assert response.status_code == 200
    rows = client.get("/api/cameras", headers={"Authorization": "Bearer u"}).json()
    row = next(item for item in rows if item["source_id"] == "pi-02/cam-1")
    assert row["pi_id"] == "pi-02"
    assert row["camera_id"] == "cam-1"


def test_snapshot_and_aoi_round_trip(client, tmp_path, monkeypatch):
    from hcdmap_backend.api import cameras as camera_api
    from hcdmap_backend.settings import settings

    settings.camera_snapshot_dir = str(tmp_path)
    published = []
    monkeypatch.setattr(camera_api, "publish_camera_aoi", lambda pi, cam, pts: published.append((pi, cam, pts)))
    image = b"\xff\xd8test-jpeg\xff\xd9"
    uploaded = client.post(
        "/api/ingest/camera-snapshot?source_id=pi-03%2Fcam-2",
        content=image,
        headers={**HEADERS, "Content-Type": "image/jpeg"},
    )
    assert uploaded.status_code == 200
    user = {"Authorization": "Bearer u"}
    fetched = client.get("/api/cameras/snapshot?source_id=pi-03%2Fcam-2", headers=user)
    assert fetched.content == image
    points = [[0.1, 0.1], [0.1, 0.9], [0.9, 0.9], [0.9, 0.1]]
    saved = client.put("/api/cameras/aoi?source_id=pi-03%2Fcam-2", json={"points": points}, headers=user)
    assert saved.status_code == 200
    assert published == [("pi-03", "cam-2", points)]
