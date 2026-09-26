"""document lease type for agent profiles

Revision ID: 0004_lease_type
Revises: 0003_sample_key
Create Date: 2026-09-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_lease_type"
down_revision: str | Sequence[str] | None = "0003_sample_key"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.add_column(
            sa.Column("lease_type", sa.String(length=32), nullable=False, server_default="commercial")
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.drop_column("lease_type")
