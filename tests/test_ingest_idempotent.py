"""Idempotency of the pickup ingest feed, against an in-memory SQLite DB."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hcdmap_backend.api.deps import get_db
from hcdmap_backend.app import create_app
from hcdmap_backend.models import Base

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
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
