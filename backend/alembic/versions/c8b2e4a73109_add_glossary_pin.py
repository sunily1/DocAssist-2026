"""add glossary pin

Revision ID: c8b2e4a73109
Revises: a17f4d89c210
Create Date: 2026-07-13 17:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8b2e4a73109"
down_revision: Union[str, Sequence[str], None] = "a17f4d89c210"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "glossary_terms",
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.alter_column("glossary_terms", "is_pinned", server_default=None)


def downgrade() -> None:
    op.drop_column("glossary_terms", "is_pinned")
