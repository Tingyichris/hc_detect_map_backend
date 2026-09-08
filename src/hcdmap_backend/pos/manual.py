"""Default adapter: no POS. Session opens/closes come from the dashboard buttons
(`POST /api/sessions/{table_id}/open|close`), so this adapter emits nothing.

Swap for RealPosAdapter once the POS integration spec is available; wire it in app startup.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from .base import PosAdapter, PosEvent


class ManualPosAdapter(PosAdapter):
    async def events(self) -> AsyncIterator[PosEvent]:
        while True:
            await asyncio.sleep(3600)
            if False:  # pragma: no cover - never yields
                yield PosEvent("table_opened", "", 0.0)
