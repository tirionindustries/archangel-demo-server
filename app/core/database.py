import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# asyncpg requires an ssl.SSLContext (not the string "require").
# We detect an external Render Postgres hostname by the presence of
# "postgres.render.com" in the URL; internal private-network URLs
# (e.g. dpg-xxx/dbname) need no SSL at all.
def _make_connect_args() -> dict:
    url = settings.database_url
    if "postgres.render.com" in url:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return {"ssl": ctx}
    return {}

engine = create_async_engine(settings.database_url, echo=False, connect_args=_make_connect_args())
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
