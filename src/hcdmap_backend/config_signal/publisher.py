"""Publish the retained sushi/<store>/config/map signal so the fusion server hot-reloads."""
from __future__ import annotations

import json
import logging
import time

from ..settings import settings

log = logging.getLogger(__name__)


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
            qos=1,
            retain=True,
        )
        log.info("published map signal v%d to %s", map_version, topic)
    except Exception as e:  # noqa: BLE001 - never fail the API call over the signal
        log.warning("could not publish map signal: %s", e)
