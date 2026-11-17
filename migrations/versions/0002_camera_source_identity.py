"""add Raspberry Pi and local camera identity

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("cameras")}
    if "pi_id" not in columns:
        op.add_column("cameras", sa.Column("pi_id", sa.String(length=64), nullable=True))
    if "local_camera_id" not in columns:
        op.add_column("cameras", sa.Column("local_camera_id", sa.String(length=64), nullable=True))
    if "snapshot_path" not in columns:
        op.add_column("cameras", sa.Column("snapshot_path", sa.String(length=512), nullable=True))
    if "snapshot_updated_at" not in columns:
        op.add_column("cameras", sa.Column("snapshot_updated_at", sa.DateTime(), nullable=True))
    if "aoi_json" not in columns:
        op.add_column("cameras", sa.Column("aoi_json", sa.Text(), nullable=True))
    indexes = {index["name"] for index in inspector.get_indexes("cameras")}
    if "ix_cameras_pi_id" not in indexes:
        op.create_index("ix_cameras_pi_id", "cameras", ["pi_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {index["name"] for index in inspector.get_indexes("cameras")}
    if "ix_cameras_pi_id" in indexes:
        op.drop_index("ix_cameras_pi_id", table_name="cameras")
    columns = {column["name"] for column in inspector.get_columns("cameras")}
    for name in ("aoi_json", "snapshot_updated_at", "snapshot_path"):
        if name in columns:
            op.drop_column("cameras", name)
    if "local_camera_id" in columns:
        op.drop_column("cameras", "local_camera_id")
    if "pi_id" in columns:
        op.drop_column("cameras", "pi_id")
