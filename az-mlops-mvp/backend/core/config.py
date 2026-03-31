from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    databricks_host: str = ""
    databricks_token: str = ""
    database_url: str = ""
    app_env: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()