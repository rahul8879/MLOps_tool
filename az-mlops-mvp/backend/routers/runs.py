

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query, status

from schemas.run import (
    CompareDeployedResponse,
    RunCompareResponse,
    RunMetricsResponse,
    RunSummary,
)
from services import run_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# DS-003: Get all runs for an experiment
# Registered on the /experiments router prefix in main.py via include_router
# but we expose it here and mount it from experiments router too.
# We add it here with full path so it sits on the /runs router cleanly.
# ---------------------------------------------------------------------------
@router.get(
    "/by-experiment/{experiment_id}",
    response_model=List[RunSummary],
    status_code=status.HTTP_200_OK,
    summary="Get all runs for an experiment (DS-003)",
    include_in_schema=False,  # hidden alias — primary route is on experiments router
)
def get_runs_for_experiment_alias(experiment_id: str):
    return _fetch_runs(experiment_id)


def _fetch_runs(experiment_id: str) -> List[RunSummary]:
    try:
        runs = run_service.get_runs_for_experiment(experiment_id)
        if not runs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No runs found for experiment '{experiment_id}'",
            )
        return runs
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("[Router:runs] get_runs(%s) failed", experiment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve runs: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# DS-006: Compare multiple runs (MUST come before /{run_id}/... routes)
# ---------------------------------------------------------------------------
@router.get(
    "/compare",
    response_model=RunCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare multiple runs side by side (DS-006)",
    response_description="Comparison of run metrics with winner recommendation",
)
def compare_runs(
    run_ids: str = Query(
        ...,
        description="Comma-separated list of run IDs to compare (e.g. abc123,def456)",
        example="abc123xyz,def456uvw",
    )
):
    """
    Compare two or more MLflow runs side by side.

    - Pass run IDs as a comma-separated query param: `?run_ids=id1,id2`
    - Returns metrics and params for each run, plus a winner recommendation
      based on accuracy and RMSE.
    """
    ids = [r.strip() for r in run_ids.split(",") if r.strip()]

    if len(ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 run IDs are required for comparison",
        )

    try:
        result = run_service.compare_runs(ids)
    except Exception as exc:
        logger.exception("[Router:runs] compare_runs failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(exc)}",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"None of the requested run IDs were found: {ids}",
        )

    return result


# ---------------------------------------------------------------------------
# DS-004: Get metrics + params for a single run
# ---------------------------------------------------------------------------
@router.get(
    "/{run_id}/metrics",
    response_model=RunMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get metrics and params for a run (DS-004)",
    response_description="Metrics, hyperparameters, and tags for the specified run",
)
def get_run_metrics(run_id: str):
    """
    Retrieve all metrics, params, and tags logged to a specific MLflow run.
    """
    try:
        result = run_service.get_run_metrics(run_id)
    except Exception as exc:
        logger.exception("[Router:runs] get_run_metrics(%s) failed", run_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics for run '{run_id}': {str(exc)}",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )

    return result


# ---------------------------------------------------------------------------
# DS-007: Compare run vs currently deployed model
# ---------------------------------------------------------------------------
@router.get(
    "/{run_id}/compare-deployed",
    response_model=CompareDeployedResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare a run against the deployed production model (DS-007)",
    response_description="Side-by-side comparison with promotion recommendation",
)
def compare_run_vs_deployed(run_id: str):
    """
    Compare a candidate MLflow run against the currently deployed production model.

    - Fetches deployed model metrics from Databricks Model Registry (Production stage).
    - Returns accuracy delta and a PROMOTE / HOLD / REJECT recommendation.
    """
    try:
        result = run_service.compare_run_vs_deployed(run_id)
    except Exception as exc:
        logger.exception("[Router:runs] compare_run_vs_deployed(%s) failed", run_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed for run '{run_id}': {str(exc)}",
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with id '{run_id}' not found",
        )

    return result
