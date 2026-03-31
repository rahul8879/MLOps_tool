from pydantic_settings import BaseSettings
from pathlib import Path

# .env file ka exact path
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

class Settings(BaseSettings):
    databricks_host: str = ""
    databricks_token: str = ""
    database_url: str = ""
    app_env: str = "development"

    class Config:
        env_file = str(ENV_PATH)

settings = Settings()
print(f"[INFO] Loaded .env from: {ENV_PATH}")