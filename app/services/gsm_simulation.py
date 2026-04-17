import asyncio
import hashlib
import random
import uuid
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class GsmDot:
    id: str
    lat: float
    lng: float
    is_flagged_threat: bool
    movement_vector_lat: float
    movement_vector_lng: float


class GsmSimulationService:
    """
    Event-driven GSM simulation. Generates a realistic population of GSM dots
    for an incident radius and continuously updates their positions.
    Threat signatures move in coordinated convergence patterns per the demo scenario.
    """

    _DEMO_LAT = 9.7795      # Kafanchan, Kaduna State
    _DEMO_LNG = 8.2982
    _RADIUS_DEG = 0.0045    # ~500m in degrees at this latitude
    _UPDATE_INTERVAL = 2.0  # seconds between position pushes

    def __init__(self):
        self._positions: dict[str, list[GsmDot]] = {}
        self._running: dict[str, bool] = {}
        self._sio = None    # injected by main.py after socket server is created

    def set_socket_server(self, sio):
        self._sio = sio

    def _generate_population(self, incident_id: str, lat: float, lng: float) -> list[GsmDot]:
        dots = []
        # 11 background/civilian numbers — slow random drift
        for _ in range(11):
            dot_lat = lat + random.uniform(-self._RADIUS_DEG, self._RADIUS_DEG)
            dot_lng = lng + random.uniform(-self._RADIUS_DEG, self._RADIUS_DEG)
            dots.append(GsmDot(
                id=hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16],
                lat=dot_lat,
                lng=dot_lng,
                is_flagged_threat=False,
                movement_vector_lat=random.uniform(-0.00002, 0.00002),
                movement_vector_lng=random.uniform(-0.00002, 0.00002),
            ))
        # 3 threat signatures — converging northeast toward incident (demo scenario)
        for i in range(3):
            dot_lat = lat + random.uniform(0.002, 0.004)
            dot_lng = lng + random.uniform(-0.003, -0.001)
            dots.append(GsmDot(
                id=hashlib.sha256(f"threat-{incident_id}-{i}".encode()).hexdigest()[:16],
                lat=dot_lat,
                lng=dot_lng,
                is_flagged_threat=True,
                movement_vector_lat=random.uniform(-0.00012, -0.00008),  # moving south toward incident
                movement_vector_lng=random.uniform(0.00008, 0.00012),    # moving east toward incident
            ))
        return dots

    async def run(self, incident_id: UUID):
        key = str(incident_id)
        self._positions[key] = self._generate_population(key, self._DEMO_LAT, self._DEMO_LNG)
        self._running[key] = True

        while self._running.get(key):
            for dot in self._positions[key]:
                dot.lat += dot.movement_vector_lat
                dot.lng += dot.movement_vector_lng

            if self._sio:
                payload = [
                    {"id": d.id, "lat": d.lat, "lng": d.lng, "flagged": d.is_flagged_threat}
                    for d in self._positions[key]
                ]
                await self._sio.emit("gsm:update", {"incident_id": key, "dots": payload})

            await asyncio.sleep(self._UPDATE_INTERVAL)

    def get_current_positions(self, incident_id: UUID) -> list[dict]:
        key = str(incident_id)
        dots = self._positions.get(key, [])
        return [{"id": d.id, "lat": d.lat, "lng": d.lng, "flagged": d.is_flagged_threat} for d in dots]

    def stop(self, incident_id: UUID):
        self._running[str(incident_id)] = False


# Module-level singleton — imported by both api/gsm.py and main.py
gsm_service = GsmSimulationService()
