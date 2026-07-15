"""add live metrics and feedback

Revision ID: a17f4d89c210
Revises: 50113d615900
Create Date: 2026-07-13 16:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a17f4d89c210"
down_revision: Union[str, Sequence[str], None] = "50113d615900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_device_type", sa.String(length=20), nullable=True))
    op.create_table(
        "service_feedback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_service_feedback_user_id", "service_feedback", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_service_feedback_user_id", table_name="service_feedback")
    op.drop_table("service_feedback")
    op.drop_column("users", "last_device_type")
    op.drop_column("users", "last_seen_at")
