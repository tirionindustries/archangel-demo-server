import asyncio
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import AsyncSessionLocal, get_db
from app.core.serializers import serialize_incident
from app.models.entities import Incident, User
from app.services.gemini_reasoning import generate_incident_brief
from app.services.gsm_simulation import gsm_service
from app.sockets.events import sio

router = APIRouter(prefix="/demo", tags=["demo"])

# Keeps background tasks alive — prevents GC before completion
_tasks: set[asyncio.Task] = set()

_DEMO_TRANSCRIPT = (
    "Armed men... they have entered the market... please send help... "
    "Kafanchan main market... about ten of them with guns..."
)


def _fire(coro) -> None:
    task = asyncio.create_task(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def _gemini_analysis(incident_id: uuid.UUID) -> None:
    await asyncio.sleep(3)  # let "active" state render first
    try:
        brief = await generate_incident_brief({
            "triggered_by": "ussd",
            "caller_status": "call_cut",
            "location": "Kafanchan, Kaduna State, Nigeria",
            "coordinates": {"lat": 9.7795, "lng": 8.2982},
            "realtime_transcript": _DEMO_TRANSCRIPT,
            "gsm_dot_count": 14,
            "flagged_threat_signatures": 3,
            "pattern": "Three GSM signatures converging from northwest toward incident location",
        })
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Incident).where(Incident.id == incident_id))
            incident = result.scalar_one_or_none()
            if incident:
                incident.threat_classification = brief.get("threat_classification")
                incident.confidence_level = brief.get("confidence_level")
                incident.gemini_brief = brief.get("operator_brief")
                incident.gemini_recommended_response = brief.get("recommended_response")
                incident.status = "operator_reviewing"
                await db.commit()
                await db.refresh(incident)
                await sio.emit("incident:updated", serialize_incident(incident))
    except Exception as exc:
        print(f"[demo] Gemini analysis error: {exc}")


@router.post("/reset")
async def reset_demo(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from sqlalchemy import update
    from datetime import datetime, timezone
    await db.execute(
        update(Incident)
        .where(Incident.status.in_(["active", "operator_reviewing", "dispatched"]))
        .values(status="resolved", resolved_at=datetime.now(timezone.utc))
    )
    await db.commit()
    # Stop all running GSM loops
    for key in list(gsm_service._running.keys()):
        gsm_service._running[key] = False
    await sio.emit("demo:reset", {})
    return {"ok": True}


@router.post("/trigger")
async def trigger_demo_incident(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    incident = Incident(
        triggered_by="ussd",
        caller_gsm="+2348012345678",
        caller_location_lat=9.7795,
        caller_location_lng=8.2982,
        resolved_location_name="Kafanchan, Kaduna State",
        status="active",
        caller_status="call_cut",
        realtime_transcript=_DEMO_TRANSCRIPT,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    await sio.emit("incident:created", serialize_incident(incident))

    _fire(gsm_service.run(incident.id))
    _fire(_gemini_analysis(incident.id))

    return serialize_incident(incident)
