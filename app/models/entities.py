import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_by: Mapped[str] = mapped_column(String(20), nullable=False)
    caller_gsm: Mapped[str | None] = mapped_column(String(20))
    caller_location_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    caller_location_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    resolved_location_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    threat_classification: Mapped[str | None] = mapped_column(String(100))
    confidence_level: Mapped[str | None] = mapped_column(String(20))
    is_proxy_report: Mapped[bool] = mapped_column(Boolean, default=False)
    proxy_target_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    proxy_target_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    caller_status: Mapped[str | None] = mapped_column(String(30))
    call_recording_path: Mapped[str | None] = mapped_column(String(500))
    call_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    gemini_brief: Mapped[str | None] = mapped_column(Text)
    gemini_recommended_response: Mapped[str | None] = mapped_column(Text)
    gemini_confidence_notes: Mapped[str | None] = mapped_column(Text)
    realtime_transcript: Mapped[str | None] = mapped_column(Text)
    operator_notes: Mapped[str | None] = mapped_column(Text)
    response_team_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("response_teams.id"))
    response_dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    events: Mapped[list["IncidentEvent"]] = relationship("IncidentEvent", back_populates="incident")
    gsm_snapshots: Mapped[list["GsmSnapshot"]] = relationship("GsmSnapshot", back_populates="incident")


class GsmSnapshot(Base):
    __tablename__ = "gsm_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    gsm_number_hash: Mapped[str | None] = mapped_column(String(64))
    lat: Mapped[float] = mapped_column(Numeric(10, 8), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(11, 8), nullable=False)
    signal_strength: Mapped[int | None] = mapped_column(Integer)
    is_flagged_threat: Mapped[bool] = mapped_column(Boolean, default=False)
    movement_vector_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    movement_vector_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="gsm_snapshots")


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("incidents.id"))
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="events")


class ResponseTeam(Base):
    __tablename__ = "response_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    base_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    current_lat: Mapped[float | None] = mapped_column(Numeric(10, 8))
    current_lng: Mapped[float | None] = mapped_column(Numeric(11, 8))
    status: Mapped[str] = mapped_column(String(30), default="available")
    estimated_response_minutes: Mapped[int | None] = mapped_column(Integer)
    equipment_level: Mapped[str | None] = mapped_column(String(30))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
