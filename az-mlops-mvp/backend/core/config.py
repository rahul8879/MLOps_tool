"""
core/config.py
==============
Centralised configuration via Pydantic BaseSettings.
All environment variables are loaded here — no os.environ calls elsewhere.

Usage:
    from core.config import settings
    print(settings.DATABRICKS_HOST)
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    APP_ENV: str = "development"
    APP_NAME: str = "AstraZeneca MLOps MVP"
    APP_VERSION: str = "1.0.0"

    # ------------------------------------------------------------------ #
    # CORS
    # ------------------------------------------------------------------ #
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ------------------------------------------------------------------ #
    # Databricks
    # ------------------------------------------------------------------ #
    DATABRICKS_HOST: Optional[str] = None
    DATABRICKS_TOKEN: Optional[str] = None

    # Model Registry settings (for compare-deployed endpoint)
    DATABRICKS_MODEL_NAME: str = "drug_efficacy_prod"
    DATABRICKS_DEPLOYED_MODEL_VERSION: str = "latest"

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str = "postgresql+psycopg2://mlops_user:mlops_pass@localhost:5432/az_mlops"

    # ------------------------------------------------------------------ #
    # Feature flags
    # ------------------------------------------------------------------ #
    @property
    def use_mock_data(self) -> bool:
        """
        Returns True when Databricks credentials are absent.
        Allows local development without a live workspace.
        """
        return not (self.DATABRICKS_HOST and self.DATABRICKS_TOKEN)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


# Singleton instance — import this everywhere
settings = Settings()
