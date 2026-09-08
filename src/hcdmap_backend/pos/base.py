"""POS integration seam. The real adapter arrives when the POS spec is provided.

The POS drives two things:
  1. session lifecycle — table opened (seated) / checked out (cleared),
  2. reconciliation — the POS bill/plate count to diff against the system's tally.
"""
from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class PosEvent:
    kind: Literal["table_opened", "table_checked_out"]
    table_id: str
    ts: float
    pos_count: int | None = None      # plates the POS thinks the table had (on checkout)
    pos_bill: float | None = None


class PosAdapter(abc.ABC):
    @abc.abstractmethod
    async def events(self) -> AsyncIterator[PosEvent]:
        """Yield POS events as they happen."""
        raise NotImplementedError
        yield  # pragma: no cover
