"""Environment-backed application settings. Credential fields never appear in repr."""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="INHERIA_", env_file=".env", extra="ignore")

    environment: str = "development"
    database_url: str = Field(default="sqlite:///./inheria.db", repr=False)
    demo_mode: bool = True
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

    @model_validator(mode="after")
    def production_configuration(self):
        if self.environment == "production":
            if self.demo_mode:
                raise ValueError("Production requires INHERIA_DEMO_MODE=false")
            if not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires a PostgreSQL database URL")
            if any(not origin.startswith("https://") for origin in self.allowed_origins):
                raise ValueError("Production allowed origins must use HTTPS")
        return self


settings = Settings()
