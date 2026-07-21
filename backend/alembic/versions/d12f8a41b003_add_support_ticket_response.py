"""add support ticket response fields

Revision ID: d12f8a41b003
Revises: c8b2e4a73109
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d12f8a41b003"
down_revision: Union[str, Sequence[str], None] = "c8b2e4a73109"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("support_tickets", sa.Column("reply_email", sa.String(length=255), nullable=True))
    op.add_column("support_tickets", sa.Column("response", sa.Text(), nullable=True))
    op.add_column(
        "support_tickets",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("support_tickets", "updated_at")
    op.drop_column("support_tickets", "response")
    op.drop_column("support_tickets", "reply_email")
