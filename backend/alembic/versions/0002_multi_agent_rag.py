"""multi-agent rag, flags, and workflow tables

Revision ID: 0002_multi_agent
Revises: 0001_initial
Create Date: 2026-09-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_multi_agent"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("documents") as batch:
        batch.add_column(sa.Column("organization_id", sa.String(length=64), nullable=False, server_default="org-harborpoint"))
        batch.add_column(sa.Column("property_id", sa.String(length=64), nullable=False, server_default="prop-unassigned"))
        batch.add_column(sa.Column("document_type", sa.String(length=32), nullable=False, server_default="lease"))
        batch.add_column(sa.Column("document_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("effective_date", sa.Date(), nullable=True))
        batch.add_column(sa.Column("lease_group_id", sa.String(length=36), nullable=True))
    op.create_index("ix_documents_lease_group_id", "documents", ["lease_group_id"])

    with op.batch_alter_table("leases") as batch:
        batch.add_column(sa.Column("organization_id", sa.String(length=64), nullable=False, server_default="org-harborpoint"))
        batch.add_column(sa.Column("property_id", sa.String(length=64), nullable=False, server_default="prop-unassigned"))
        batch.add_column(sa.Column("approval_source", sa.String(length=32), nullable=True))

    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("lease_id", sa.String(length=36), nullable=True),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("document_version", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("chunk_ordinal", sa.Integer(), nullable=False),
        sa.Column("section_heading", sa.String(length=255), nullable=False),
        sa.Column("start_page", sa.Integer(), nullable=False),
        sa.Column("end_page", sa.Integer(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("embedding_model", sa.String(length=64), nullable=False),
        sa.Column("embedding_version", sa.String(length=16), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("document_id", "content_hash", name="uq_chunks_document_hash"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_lease_id", "document_chunks", ["lease_id"])
    op.create_index("ix_document_chunks_organization_id", "document_chunks", ["organization_id"])
    op.create_index("ix_document_chunks_property_id", "document_chunks", ["property_id"])
    op.create_index(
        "ix_document_chunks_scope",
        "document_chunks",
        ["organization_id", "property_id", "document_type", "document_version"],
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("scope_type", sa.String(length=16), nullable=False),
        sa.Column("scope_id", sa.String(length=64), nullable=False),
        sa.Column("flag_key", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("config_version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("scope_type", "scope_id", "flag_key", name="uq_feature_flags_scope_key"),
    )

    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("lease_id", sa.String(length=36), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("flag_version", sa.Integer(), nullable=False),
        sa.Column("policy_result", sa.String(length=32), nullable=True),
        sa.Column("recommendation", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_workflow_executions_lease_id", "workflow_executions", ["lease_id"])

    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_executions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_executions_workflow_id", "agent_executions", ["workflow_id"])

    op.create_table(
        "mcp_tool_calls",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("server_name", sa.String(length=64), nullable=False),
        sa.Column("tool_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_executions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mcp_tool_calls_workflow_id", "mcp_tool_calls", ["workflow_id"])

    op.create_table(
        "policy_evaluations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("lease_id", sa.String(length=36), nullable=False),
        sa.Column("lease_version", sa.Integer(), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason_codes", sa.JSON(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_executions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_policy_evaluations_workflow_id", "policy_evaluations", ["workflow_id"])


def downgrade() -> None:
    op.drop_table("policy_evaluations")
    op.drop_table("mcp_tool_calls")
    op.drop_table("agent_executions")
    op.drop_table("workflow_executions")
    op.drop_table("feature_flags")
    op.drop_table("document_chunks")
    op.drop_index("ix_documents_lease_group_id", table_name="documents")
    with op.batch_alter_table("leases") as batch:
        batch.drop_column("approval_source")
        batch.drop_column("property_id")
        batch.drop_column("organization_id")
    with op.batch_alter_table("documents") as batch:
        batch.drop_column("lease_group_id")
        batch.drop_column("effective_date")
        batch.drop_column("document_version")
        batch.drop_column("document_type")
        batch.drop_column("property_id")
        batch.drop_column("organization_id")
