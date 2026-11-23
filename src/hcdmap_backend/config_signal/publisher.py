"""Publish the retained sushi/<store>/config/map signal so the fusion server hot-reloads."""
from __future__ import annotations

import json
import logging
import time

from ..settings import settings

log = logging.getLogger(__name__)


def _auth() -> dict[str, str] | None:
    if not settings.mqtt_username:
        return None
    return {
        "username": settings.mqtt_username,
        "password": settings.mqtt_password,
    }


def publish_map_signal(store_id: str, map_version: int) -> None:
    payload = json.dumps({"v": 1, "map_version": map_version, "ts": time.time()})
    topic = f"sushi/{store_id}/config/map"
    try:
        import paho.mqtt.publish as publish

        publish.single(
            topic,
            payload=payload,
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            auth=_auth(),
            qos=1,
            retain=True,
        )
        log.info("published map signal v%d to %s", map_version, topic)
    except Exception as e:  # noqa: BLE001 - never fail the API call over the signal
        log.warning("could not publish map signal: %s", e)


def publish_camera_aoi(pi_id: str, camera_id: str, points: list[list[float]]) -> None:
    topic = f"sushi/{pi_id}/config/{camera_id}/aoi"
    payload = json.dumps({"points": points, "ts": time.time()}, separators=(",", ":"))
    try:
        import paho.mqtt.publish as publish
        publish.single(
            topic,
            payload=payload,
            hostname=settings.mqtt_host,
            port=settings.mqtt_port,
            auth=_auth(),
            qos=1,
            retain=True,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("could not publish camera AOI: %s", e)


def publish_camera_screenshot_request(pi_id: str, camera_id: str, request_id: str) -> None:
    topic = f"sushi/{pi_id}/commands/{camera_id}/screenshot"
    payload = json.dumps({"request_id": request_id, "ts": time.time()}, separators=(",", ":"))
    try:
        import paho.mqtt.publish as publish
        publish.single(topic, payload=payload, hostname=settings.mqtt_host,
                       port=settings.mqtt_port, auth=_auth(), qos=1, retain=False)
    except Exception as e:  # noqa: BLE001
        log.warning("could not publish camera screenshot request: %s", e)
