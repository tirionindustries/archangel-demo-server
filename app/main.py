from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api import auth, demo, gsm, incidents, teams
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import hash_password
from app.models import entities  # noqa: F401 — registers all ORM models
from app.models.entities import ResponseTeam, User
from app.services.gsm_simulation import gsm_service
from app.sockets.events import sio


async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _seed_demo_data() -> None:
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(User).where(User.email == "operator@archangel.demo"))
        if not existing.scalar_one_or_none():
            db.add(User(
                name="Musa Ibrahim",
                email="operator@archangel.demo",
                password_hash=hash_password("archangel2026"),
                role="operator",
            ))

        rt04 = await db.execute(select(ResponseTeam).where(ResponseTeam.name == "Kafanchan Rapid Response"))
        if not rt04.scalar_one_or_none():
            db.add(ResponseTeam(
                name="Kafanchan Rapid Response",
                base_lat=9.7634, base_lng=8.3084,
                current_lat=9.7634, current_lng=8.3084,
                status="available",
                estimated_response_minutes=18,
                equipment_level="standard",
            ))

        rt07 = await db.execute(select(ResponseTeam).where(ResponseTeam.name == "Kaduna State Reserve"))
        if not rt07.scalar_one_or_none():
            db.add(ResponseTeam(
                name="Kaduna State Reserve",
                base_lat=10.5264, base_lng=7.4382,
                current_lat=10.5264, current_lng=7.4382,
                status="available",
                estimated_response_minutes=34,
                equipment_level="heavy",
            ))

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_db()
    await _seed_demo_data()
    gsm_service.set_socket_server(sio)
    yield
    await engine.dispose()


app = FastAPI(title="Archangel Demo API", version="1.0.0", lifespan=lifespan)

_origins = ["*"] if settings.frontend_url == "*" else [settings.frontend_url]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(gsm.router, prefix="/api")
app.include_router(demo.router, prefix="/api")

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
