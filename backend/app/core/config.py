from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from uuid import UUID

from pydantic import EmailStr, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Enterprise CRM API"
    environment: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str
    default_organization_id: UUID
    default_organization_name: str = "Enterprise CRM"
    default_role_name: str | None = None
    allow_self_registration: bool = False
    attachment_storage_backend: Literal["disabled", "local"] = "disabled"
    attachment_local_storage_path: Path | None = None
    attachment_max_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    import_export_max_upload_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    import_export_max_rows: int = Field(default=5_000, gt=0)
    http_max_request_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    default_admin_email: EmailStr | None = None
    default_admin_password: SecretStr | None = None
    default_admin_first_name: str | None = None
    default_admin_last_name: str | None = None
    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=15, gt=0)
    jwt_refresh_token_expire_days: int = Field(default=7, gt=0)
    jwt_issuer: str = "enterprise-crm"
    jwt_audience: str = "enterprise-crm-api"
    ollama_enabled: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma3:4b"
    ollama_timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    quote_approval_discount_threshold: float = Field(default=20.0, ge=0, le=100)

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Self:
        minimum_bytes = {"HS256": 32, "HS384": 48, "HS512": 64}
        secret_length = len(self.jwt_secret.get_secret_value().encode("utf-8"))
        if secret_length < minimum_bytes[self.jwt_algorithm]:
            raise ValueError(
                f"JWT_SECRET must contain at least {minimum_bytes[self.jwt_algorithm]} bytes "
                f"when using {self.jwt_algorithm}"
            )
        if not self.jwt_issuer.strip():
            raise ValueError("JWT_ISSUER must not be blank")
        if not self.jwt_audience.strip():
            raise ValueError("JWT_AUDIENCE must not be blank")
        if self.ollama_enabled:
            normalized_ollama = self.ollama_base_url.strip().rstrip("/")
            if not normalized_ollama.startswith(("http://127.0.0.1:", "http://localhost:")):
                raise ValueError("OLLAMA_BASE_URL must point to localhost when local AI is enabled")
            self.ollama_base_url = normalized_ollama
            if not self.ollama_model.strip():
                raise ValueError("OLLAMA_MODEL must not be blank")
        if (
            self.attachment_storage_backend == "local"
            and self.attachment_local_storage_path is None
        ):
            raise ValueError(
                "ATTACHMENT_LOCAL_STORAGE_PATH is required when "
                "ATTACHMENT_STORAGE_BACKEND=local"
            )
        if self.environment == "production" and self.database_url.startswith("sqlite"):
            raise ValueError("SQLite is not supported when ENVIRONMENT=production")
        if (
            self.environment == "production"
            and self.attachment_storage_backend != "disabled"
        ):
            raise ValueError(
                "ATTACHMENT_STORAGE_BACKEND must be disabled in production until "
                "a durable storage backend is configured"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
