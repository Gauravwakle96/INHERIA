"""Environment-backed application settings. Credential fields never appear in repr."""

from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INHERIA_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = Field(default="sqlite:///./inheria.db", repr=False)
    render_external_url: str = Field(default="", validation_alias="RENDER_EXTERNAL_URL")
    demo_mode: bool = True
    judge_demo_enabled: bool = True
    judge_demo_hours: int = Field(default=4, ge=1, le=12)
    judge_demo_max_visits: int = Field(default=40, ge=1, le=200)
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8010",
        "http://127.0.0.1:8010",
    ]
    session_hours: int = Field(default=12, ge=1, le=168)
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1024, le=50 * 1024 * 1024)
    max_document_chars: int = Field(default=500_000, ge=1000, le=2_000_000)
    retention_days: int = Field(default=365, ge=1, le=3650)
    token_encryption_key: str = Field(default="", repr=False)
    github_request_limit: int = Field(default=30, ge=1, le=100)
    llm_api_key: str = Field(default="", repr=False)
    llm_base_url: str = ""
    llm_model: str = ""
    llm_enabled: bool = False
    llm_timeout_seconds: int = Field(default=30, ge=5, le=120)
    llm_max_sources: int = Field(default=20, ge=1, le=50)

    @property
    def secure_cookies(self) -> bool:
        return self.environment == "production"

    @field_validator("database_url", mode="before")
    @classmethod
    def postgres_driver(cls, value: str) -> str:
        # Provider connection strings omit SQLAlchemy's installed psycopg v3 driver.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix) :]
        return value

    @model_validator(mode="after")
    def production_configuration(self):
        if self.environment == "production":
            if self.render_external_url and "allowed_origins" not in self.model_fields_set:
                self.allowed_origins = [self.render_external_url]
            if self.demo_mode:
                raise ValueError("Production requires INHERIA_DEMO_MODE=false")
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires a PostgreSQL database URL")
            if not self.allowed_origins:
                raise ValueError("Production requires at least one allowed HTTPS origin")
            for origin in self.allowed_origins:
                parsed = urlsplit(origin)
                if (
                    parsed.scheme != "https"
                    or not parsed.hostname
                    or parsed.username
                    or parsed.password
                    or parsed.path
                    or parsed.query
                    or parsed.fragment
                ):
                    raise ValueError("Production allowed origins must be exact HTTPS origins")
        return self


settings = Settings()
