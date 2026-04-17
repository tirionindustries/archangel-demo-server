from app.models.entities import Incident, ResponseTeam


def serialize_incident(incident: Incident) -> dict:
    return {
        "id": str(incident.id),
        "triggered_by": incident.triggered_by,
        "caller_location_lat": float(incident.caller_location_lat) if incident.caller_location_lat is not None else None,
        "caller_location_lng": float(incident.caller_location_lng) if incident.caller_location_lng is not None else None,
        "resolved_location_name": incident.resolved_location_name,
        "status": incident.status,
        "threat_classification": incident.threat_classification,
        "confidence_level": incident.confidence_level,
        "caller_status": incident.caller_status,
        "gemini_brief": incident.gemini_brief,
        "gemini_recommended_response": incident.gemini_recommended_response,
        "realtime_transcript": incident.realtime_transcript,
        "response_team_id": str(incident.response_team_id) if incident.response_team_id else None,
        "response_dispatched_at": incident.response_dispatched_at.isoformat() if incident.response_dispatched_at else None,
        "created_at": incident.created_at.isoformat(),
    }


def serialize_team(team: ResponseTeam) -> dict:
    def f(v):
        return float(v) if v is not None else None

    return {
        "id": str(team.id),
        "name": team.name,
        "status": team.status,
        "base_lat": f(team.base_lat),
        "base_lng": f(team.base_lng),
        "current_lat": f(team.current_lat),
        "current_lng": f(team.current_lng),
        "estimated_response_minutes": team.estimated_response_minutes,
        "equipment_level": team.equipment_level,
    }
