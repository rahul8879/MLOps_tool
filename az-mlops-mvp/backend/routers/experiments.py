
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from schemas.experiment import ExperimentDetail, ExperimentSummary
from services import experiment_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# DS-001: List all experiments
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=List[ExperimentSummary],
    status_code=status.HTTP_200_OK,
    summary="List all MLflow experiments (DS-001)",
    response_description="Array of experiment summaries from Databricks",
)
def list_experiments():
    """
    Retrieve all MLflow experiments from the connected Databricks workspace.

    - Returns a flat list of experiment summaries (id, name, lifecycle, created_at).
    - Falls back to mock data if Databricks credentials are not configured.
    """
    try:
        return experiment_service.list_experiments()
    except Exception as exc:
        logger.exception("[Router:experiments] list_experiments failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve experiments: {str(exc)}",
        )


@router.get(
    "/{experiment_id}",
    response_model=ExperimentDetail,
    status_code=status.HTTP_200_OK,
    summary="Get experiment by ID (DS-002)",
    response_description="Full experiment detail including tags and artifact location",
)
def get_experiment(experiment_id: str):
    """
    Retrieve full details of a single experiment by its Databricks MLflow ID.

    - Includes artifact_location and tags (team, brand, market, etc.).
    - Returns 404 if the experiment ID does not exist.
    """
    try:
        experiment = experiment_service.get_experiment_by_id(experiment_id)
    except Exception as exc:
        logger.exception("[Router:experiments] get_experiment(%s) failed", experiment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve experiment {experiment_id}: {str(exc)}",
        )

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with id '{experiment_id}' not found",
        )

    return experiment
