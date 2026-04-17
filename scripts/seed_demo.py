"""
Seed the demo database with an operator account and the two response teams
used in the Section 13 demo scenario (RT-04 Kafanchan, RT-07 Kaduna Reserve).

Run: python scripts/seed_demo.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.entities import ResponseTeam, User


async def seed():
    async with AsyncSessionLocal() as db:
        # Default operator — change password before any real demo
        existing = await db.execute(select(User).where(User.email == "operator@archangel.demo"))
        if not existing.scalar_one_or_none():
            db.add(User(
                name="Musa Ibrahim",
                email="operator@archangel.demo",
                password_hash=hash_password("archangel2026"),
                role="operator",
            ))
            print("Created operator: operator@archangel.demo / archangel2026")

        # RT-04 — Kafanchan Rapid Response (demo scenario primary team)
        rt04 = await db.execute(select(ResponseTeam).where(ResponseTeam.name == "Kafanchan Rapid Response"))
        if not rt04.scalar_one_or_none():
            db.add(ResponseTeam(
                name="Kafanchan Rapid Response",
                base_lat=9.7634,
                base_lng=8.3084,
                current_lat=9.7634,
                current_lng=8.3084,
                status="available",
                estimated_response_minutes=18,
                equipment_level="standard",
            ))
            print("Created RT-04: Kafanchan Rapid Response")

        # RT-07 — Kaduna State Reserve (demo scenario standby team)
        rt07 = await db.execute(select(ResponseTeam).where(ResponseTeam.name == "Kaduna State Reserve"))
        if not rt07.scalar_one_or_none():
            db.add(ResponseTeam(
                name="Kaduna State Reserve",
                base_lat=10.5264,
                base_lng=7.4382,
                current_lat=10.5264,
                current_lng=7.4382,
                status="available",
                estimated_response_minutes=34,
                equipment_level="heavy",
            ))
            print("Created RT-07: Kaduna State Reserve")

        await db.commit()
        print("Seed complete.")


asyncio.run(seed())
