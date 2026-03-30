

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from routers import experiments, runs, submissions
from services.run_service import get_runs_for_experiment
from schemas.run import RunSummary
from typing import List
from fastapi import APIRouter, HTTPException, status

logging.basicConfig(
    level=logging.DEBUG if settings.APP_ENV == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown lifecycle."""
    logger.info("AZ MLOps MVP starting in '%s' mode", settings.APP_ENV)
    logger.info(
        "Databricks host: %s",
        settings.DATABRICKS_HOST or "NOT SET (mock mode active)",
    )
    yield
    logger.info("AZ MLOps MVP shutting down")


app = FastAPI(
    title="AstraZeneca MLOps MVP API",
    description=(
        "**Sprint 1 — Data Scientist Persona**\n\n"
        "Endpoints for browsing Databricks MLflow experiments, inspecting run metrics, "
        "comparing runs, benchmarking against the deployed model, and submitting runs for "
        "admin review.\n\n"
        "When `DATABRICKS_HOST`/`DATABRICKS_TOKEN` are absent, all Databricks-backed "
        "endpoints automatically return realistic mock data so local development works "
        "without credentials."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# DS-003 inline router — GET /experiments/{experiment_id}/runs
# Defined here so it sits cleanly under the /experiments prefix.
# ---------------------------------------------------------------------------
_exp_runs_router = APIRouter()


@_exp_runs_router.get(
    "/{experiment_id}/runs",
    response_model=List[RunSummary],
    status_code=status.HTTP_200_OK,
    summary="Get all runs for an experiment (DS-003)",
    tags=["Experiments"],
)
def get_runs_for_experiment_endpoint(experiment_id: str):
    """
    Retrieve all MLflow runs belonging to the given experiment.

    Includes per-run metrics and hyperparameters (params).
    Returns 404 if the experiment has no runs.
    """
    try:
        run_list = get_runs_for_experiment(experiment_id)
    except Exception as exc:
        logger.exception("get_runs_for_experiment(%s) failed", experiment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve runs: {str(exc)}",
        )

    if not run_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No runs found for experiment '{experiment_id}'",
        )
    return run_list


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
app.include_router(_exp_runs_router, prefix="/experiments", tags=["Experiments"])
app.include_router(runs.router, prefix="/runs", tags=["Runs"])
app.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])


# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    """Liveness probe."""
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "version": "1.0.0",
        "mock_mode": settings.use_mock_data,
    }


@app.get("/", tags=["Health"])
def root():
    return {
        "message": " MLOps MVP API",
        "docs": "/docs",
        "health": "/health",
    }
