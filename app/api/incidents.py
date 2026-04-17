from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.serializers import serialize_incident, serialize_team
from app.models.entities import Incident, IncidentEvent, ResponseTeam, User
from app.services.gsm_simulation import gsm_service
from app.sockets.events import sio

router = APIRouter(prefix="/incidents", tags=["incidents"])


class DispatchBody(BaseModel):
    team_id: UUID


class ResolveBody(BaseModel):
    outcome_notes: str


@router.get("/active")
async def get_active_incidents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Incident).where(Incident.status.in_(["active", "operator_reviewing", "dispatched"]))
    )
    return result.scalars().all()


@router.get("/{incident_id}")
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}/dispatch")
async def dispatch_incident(
    incident_id: UUID,
    body: DispatchBody,
    db: AsyncSession = Depends(get_db),
    operator: User = Depends(get_current_user),
):
    from datetime import datetime, timezone
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = "dispatched"
    incident.response_team_id = body.team_id
    incident.response_dispatched_at = datetime.now(timezone.utc)
    event = IncidentEvent(incident_id=incident_id, event_type="response_dispatched", actor_id=operator.id)
    db.add(event)
    team_result = await db.execute(select(ResponseTeam).where(ResponseTeam.id == body.team_id))
    team = team_result.scalar_one_or_none()
    if team:
        team.status = "dispatched"
    await db.commit()
    await db.refresh(incident)
    if team:
        await db.refresh(team)
        await sio.emit("team:updated", serialize_team(team))
    await sio.emit("incident:updated", serialize_incident(incident))
    return serialize_incident(incident)


@router.patch("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: UUID,
    body: ResolveBody,
    db: AsyncSession = Depends(get_db),
    operator: User = Depends(get_current_user),
):
    from datetime import datetime, timezone
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    incident.status = "resolved"
    incident.outcome_notes = body.outcome_notes
    incident.resolved_at = datetime.now(timezone.utc)
    event = IncidentEvent(incident_id=incident_id, event_type="resolved", actor_id=operator.id)
    db.add(event)
    await db.commit()
    await db.refresh(incident)
    gsm_service.stop(incident_id)
    if incident.response_team_id:
        team_result = await db.execute(select(ResponseTeam).where(ResponseTeam.id == incident.response_team_id))
        team = team_result.scalar_one_or_none()
        if team:
            team.status = "available"
            await db.commit()
            await db.refresh(team)
            await sio.emit("team:updated", serialize_team(team))
    await sio.emit("incident:updated", serialize_incident(incident))
    return serialize_incident(incident)
