"""Table-session state machine.

A session runs from seat to clear. Pickups attach to the table's currently-open session.
Clear signal priority: POS (when wired) > manual dashboard button > auto-heuristic nudge only.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import TableSession


def attach_to_open_session(db: Session, store_id: str, table_id: str, ts: float) -> int:
    """Return the id of the open session for this table, creating one if none is open.

    Auto-opening on first pickup is a reasonable default until the POS feed drives opens.
    """
    row = db.scalar(
        select(TableSession).where(
            TableSession.store_id == store_id,
            TableSession.table_id == table_id,
            TableSession.status == "open",
        )
    )
    if row is None:
        row = TableSession(
            store_id=store_id,
            table_id=table_id,
            status="open",
            opened_at=datetime.utcfromtimestamp(ts),
        )
        db.add(row)
        db.flush()
    return row.id
