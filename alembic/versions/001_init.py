"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "response_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("base_lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("base_lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("current_lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("current_lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("status", sa.String(30), server_default="available"),
        sa.Column("estimated_response_minutes", sa.Integer(), nullable=True),
        sa.Column("equipment_level", sa.String(30), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("triggered_by", sa.String(20), nullable=False),
        sa.Column("caller_gsm", sa.String(20), nullable=True),
        sa.Column("caller_location_lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("caller_location_lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("resolved_location_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("threat_classification", sa.String(100), nullable=True),
        sa.Column("confidence_level", sa.String(20), nullable=True),
        sa.Column("is_proxy_report", sa.Boolean(), server_default=sa.false()),
        sa.Column("proxy_target_lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("proxy_target_lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("caller_status", sa.String(30), nullable=True),
        sa.Column("call_recording_path", sa.String(500), nullable=True),
        sa.Column("call_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("gemini_brief", sa.Text(), nullable=True),
        sa.Column("gemini_recommended_response", sa.Text(), nullable=True),
        sa.Column("gemini_confidence_notes", sa.Text(), nullable=True),
        sa.Column("realtime_transcript", sa.Text(), nullable=True),
        sa.Column("operator_notes", sa.Text(), nullable=True),
        sa.Column("response_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("response_teams.id"), nullable=True),
        sa.Column("response_dispatched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_arrived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "gsm_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=True),
        sa.Column("gsm_number_hash", sa.String(64), nullable=True),
        sa.Column("lat", sa.Numeric(10, 8), nullable=False),
        sa.Column("lng", sa.Numeric(11, 8), nullable=False),
        sa.Column("signal_strength", sa.Integer(), nullable=True),
        sa.Column("is_flagged_threat", sa.Boolean(), server_default=sa.false()),
        sa.Column("movement_vector_lat", sa.Numeric(10, 8), nullable=True),
        sa.Column("movement_vector_lng", sa.Numeric(11, 8), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("incident_events")
    op.drop_table("gsm_snapshots")
    op.drop_table("incidents")
    op.drop_table("response_teams")
    op.drop_table("users")
