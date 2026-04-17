from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.serializers import serialize_team
from app.models.entities import ResponseTeam, User

router = APIRouter(prefix="/teams", tags=["teams"])


class LocationUpdate(BaseModel):
    lat: float
    lng: float


@router.get("")
async def get_all_teams(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(ResponseTeam))
    return [serialize_team(t) for t in result.scalars().all()]


@router.get("/available")
async def get_available_teams(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(ResponseTeam).where(ResponseTeam.status == "available"))
    return [serialize_team(t) for t in result.scalars().all()]


@router.post("/{team_id}/location")
async def update_team_location(
    team_id: UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ResponseTeam).where(ResponseTeam.id == team_id))
    team = result.scalar_one_or_none()
    if team:
        team.current_lat = body.lat
        team.current_lng = body.lng
        await db.commit()
    return {"ok": True}
