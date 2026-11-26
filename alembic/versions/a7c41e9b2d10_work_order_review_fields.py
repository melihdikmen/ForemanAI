"""work order review fields: approved_* -> reviewed_*, add rejection_reason

A foreman can approve OR reject, so the reviewer columns are renamed to cover both,
and a rejection reason is stored so the technician knows why.

Revision ID: a7c41e9b2d10
Revises: f3a13cc322dc
Create Date: 2026-11-26 18:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7c41e9b2d10"
down_revision: str | Sequence[str] | None = "f3a13cc322dc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename reviewer columns (keeps existing data) and add rejection_reason."""
    op.alter_column("work_orders", "approved_by", new_column_name="reviewed_by")
    op.alter_column("work_orders", "approved_at", new_column_name="reviewed_at")
    op.add_column("work_orders", sa.Column("rejection_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    """Revert to the original approved_* columns."""
    op.drop_column("work_orders", "rejection_reason")
    op.alter_column("work_orders", "reviewed_at", new_column_name="approved_at")
    op.alter_column("work_orders", "reviewed_by", new_column_name="approved_by")
