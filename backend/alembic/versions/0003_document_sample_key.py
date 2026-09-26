"""explicit sample key for fixture matching

Revision ID: 0003_sample_key
Revises: 0002_multi_agent
Create Date: 2026-09-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_sample_key"
down_revision: str | Sequence[str] | None = "0002_multi_agent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.add_column(sa.Column("sample_key", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.drop_column("sample_key")
