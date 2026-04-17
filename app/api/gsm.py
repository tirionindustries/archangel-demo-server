from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.entities import User
from app.services.gsm_simulation import gsm_service

router = APIRouter(prefix="/gsm", tags=["gsm"])


@router.post("/simulate/{incident_id}")
async def start_simulation(
    incident_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    background_tasks.add_task(gsm_service.run, incident_id)
    return {"started": True, "incident_id": str(incident_id)}


@router.get("/snapshot/{incident_id}")
async def get_snapshot(
    incident_id: UUID,
    _: User = Depends(get_current_user),
):
    return gsm_service.get_current_positions(incident_id)
