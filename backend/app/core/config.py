from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _default_database_url() -> str:
    path = (_REPO_ROOT / "data" / "fineguard.db").resolve()
    return f"sqlite+aiosqlite:///{path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", str(_REPO_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default_factory=_default_database_url)
    api_v1_prefix: str = Field(default="/api/v1", validation_alias="API_V1_PREFIX")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )
    api_version: str = "0.1.0"
    model_version: str = "stub-0.1.0"

    @field_validator("database_url", mode="before")
    @classmethod
    def resolve_relative_sqlite(cls, v: object) -> object:
        if not isinstance(v, str):
            return v
        if v.startswith("sqlite+aiosqlite:///./"):
            rel = v.removeprefix("sqlite+aiosqlite:///./")
            path = (_REPO_ROOT / rel).resolve()
            return f"sqlite+aiosqlite:///{path.as_posix()}"
        return v

    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
