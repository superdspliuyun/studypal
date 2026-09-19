"""Application configuration loaded from environment via pydantic-settings.

The DEV_PLACEHOLDER secret is rejected when ENV != "dev" so a misconfigured
production deploy fails fast instead of signing tokens with a known string.

The DeepSeek API key is required in all environments — the assistant cannot
degrade gracefully without it — so an empty key also fails fast at startup.
"""

from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEV_PLACEHOLDER_SECRET = "<dev-only-placeholder-change-me>"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default="sqlite:///./studypal.db", alias="DATABASE_URL")
    jwt_secret: str = Field(default=DEV_PLACEHOLDER_SECRET, alias="JWT_SECRET")
    jwt_access_ttl_min: int = Field(default=15, alias="JWT_ACCESS_TTL_MIN", ge=1)
    jwt_refresh_ttl_day: int = Field(default=7, alias="JWT_REFRESH_TTL_DAY", ge=1)
    cors_allow_origins: str = Field(
        default="http://localhost:5173", alias="CORS_ALLOW_ORIGINS"
    )
    env: str = Field(default="dev", alias="ENV")

    # DeepSeek (OpenAI-compatible) configuration.
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    @field_validator("env")
    @classmethod
    def _normalize_env(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"dev", "prod"}:
            raise ValueError(f"ENV must be 'dev' or 'prod', got {v!r}")
        return v

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    def assert_production_secret(self) -> None:
        """Raise if running in non-dev with the placeholder JWT secret."""
        if not self.is_dev and self.jwt_secret == DEV_PLACEHOLDER_SECRET:
            raise RuntimeError(
                "JWT_SECRET must be set explicitly when ENV != 'dev'. "
                "Refusing to start with the placeholder secret."
            )

    def assert_deepseek_config(self) -> None:
        """Raise if DEEPSEEK_API_KEY is empty in any environment.

        The assistant cannot meaningfully degrade without a key — better to
        fail fast at startup than silently returning 5xx on every chat call.
        """
        if not self.deepseek_api_key.strip():
            raise RuntimeError(
                "DEEPSEEK_API_KEY must be set in every environment. "
                "Refusing to start with an empty key."
            )


settings = Settings()
settings.assert_production_secret()
settings.assert_deepseek_config()