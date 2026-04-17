from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    jwt_secret: str
    jwt_expiry_hours: int = 8
    demo_mode: bool = True
    incident_radius_meters: int = 500
    call_cut_escalation_seconds: int = 90
    frontend_url: str = "*"

    @field_validator("database_url", mode="before")
    @classmethod
    def coerce_asyncpg_url(cls, v: str) -> str:
        # Render provides postgres:// or postgresql:// — asyncpg needs postgresql+asyncpg://
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
