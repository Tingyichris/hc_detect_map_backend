from datetime import datetime, timedelta

from hcdmap_backend.api.cameras import camera_payload
from hcdmap_backend.models import Camera


def camera(**overrides) -> Camera:
    values = {
        "id": "pi-01/cam-1",
        "store_id": "store-001",
        "pi_id": "pi-01",
        "local_camera_id": "cam-1",
        "snapshot_path": None,
        "snapshot_updated_at": None,
        "aoi_json": None,
        "role": "table",
        "table_id": None,
        "state": "online",
        "last_reason": "ok",
        "last_seen_at": datetime(2026, 1, 1, 12, 0, 0),
        "occluded_seconds_today": 0.0,
        "dropped_msgs_today": 0,
    }
    values.update(overrides)
    return Camera(**values)


def test_legacy_seed_camera_without_mqtt_registration_is_hidden():
    assert camera_payload(camera(pi_id=None, last_seen_at=None)) is None


def test_online_state_remains_until_mqtt_reports_disconnect():
    last_seen = datetime(2026, 1, 1, 12, 0, 0)
    payload = camera_payload(camera(last_seen_at=last_seen), last_seen + timedelta(seconds=31))
    assert payload is not None
    assert payload["state"] == "online"
    assert payload["last_reason"] == "ok"


def test_recent_online_status_is_online():
    last_seen = datetime(2026, 1, 1, 12, 0, 0)
    payload = camera_payload(camera(last_seen_at=last_seen), last_seen + timedelta(seconds=10))
    assert payload is not None
    assert payload["state"] == "online"
