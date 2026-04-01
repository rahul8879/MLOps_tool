from pydantic_settings import BaseSettings
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    databricks_host: str = ""
    databricks_token: str = ""
    database_url: str = ""
    app_env: str = "development"  # "development" or "production"

    # Databricks Apps root path
    app_root_path: str = ""

    class Config:
        env_file = str(ENV_PATH)

settings = Settings()