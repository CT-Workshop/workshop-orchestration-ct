"""initial schema

Revision ID: 20260912_0001
Revises:
Create Date: 2026-09-12

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260912_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "closing_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("external_ref", sa.String(128), nullable=True, index=True),
        sa.Column("lender_org_id", sa.String(64), nullable=False, index=True),
        sa.Column("title_company_id", sa.String(64), nullable=True, index=True),
        sa.Column("borrower_display_name", sa.String(256), nullable=True),
        sa.Column("borrower_contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("state", sa.String(32), nullable=False, index=True),
        sa.Column("scheduled_signing_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("los_callback_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "workflow_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closing_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("from_state", sa.String(32), nullable=True),
        sa.Column("to_state", sa.String(32), nullable=False, index=True),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(128), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.ForeignKeyConstraint(["closing_id"], ["closing_cases.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "notary_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closing_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("notary_id", sa.String(64), nullable=False, index=True),
        sa.Column("signing_agency_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["closing_id"], ["closing_cases.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "closing_id",
            "notary_id",
            name="uq_notary_assignment_closing_notary",
        ),
    )
    op.create_table(
        "funding_checklists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("closing_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("all_cleared", sa.Boolean(), nullable=False, index=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated_by", sa.String(64), nullable=True),
        sa.ForeignKeyConstraint(["closing_id"], ["closing_cases.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "partner_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("partner_id", sa.String(64), nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("idempotency_key", sa.String(128), nullable=True, index=True),
        sa.Column("raw_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("headers_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processed_ok", sa.Boolean(), nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.UniqueConstraint(
            "partner_id",
            "idempotency_key",
            name="uq_partner_webhook_partner_idempotency",
        ),
    )


def downgrade() -> None:
    op.drop_table("partner_webhook_events")
    op.drop_table("funding_checklists")
    op.drop_table("notary_assignments")
    op.drop_table("workflow_events")
    op.drop_table("closing_cases")
