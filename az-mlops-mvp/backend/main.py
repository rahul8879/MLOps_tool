from fastapi import FastAPI
from routers import experiments, runs
from core.config import settings

app = FastAPI(
    title="AstraZeneca MLOps MVP",
    version="0.1.0",
    root_path=settings.app_root_path
)

app.include_router(experiments.router, prefix="/api")
app.include_router(runs.router, prefix="/api")

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "env": settings.app_env
    }