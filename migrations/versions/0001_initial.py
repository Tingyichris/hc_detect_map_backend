"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-08

Generate real DDL once the DB is reachable:
    alembic revision --autogenerate -m "initial"
against models/. This placeholder just creates tables from metadata so `alembic upgrade head`
works on a fresh dev DB.
"""
from __future__ import annotations

from alembic import op

from hcdmap_backend.models import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
