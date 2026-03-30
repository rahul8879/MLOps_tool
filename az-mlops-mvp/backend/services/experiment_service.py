

import logging
from datetime import datetime, timezone
from typing import List

from core.databricks_client import get_workspace_client
from core.config import settings
from schemas.experiment import ExperimentDetail, ExperimentSummary

logger = logging.getLogger(__name__)


MOCK_EXPERIMENTS = [
    {
        "experiment_id": "1",
        "name": "drug_efficacy_xgboost_v1",
        "artifact_location": "dbfs:/mlflow/experiments/1",
        "lifecycle_stage": "active",
        "tags": {"team": "commercial_ai", "market": "UK", "brand": "Tagrisso"},
        "created_at": datetime(2026, 3, 28, 10, 0, 0, tzinfo=timezone.utc),
    },
    {
        "experiment_id": "2",
        "name": "drug_efficacy_lightgbm_v2",
        "artifact_location": "dbfs:/mlflow/experiments/2",
        "lifecycle_stage": "active",
        "tags": {"team": "commercial_ai", "market": "DE", "brand": "Imfinzi"},
        "created_at": datetime(2026, 3, 29, 9, 0, 0, tzinfo=timezone.utc),
    },
    {
        "experiment_id": "3",
        "name": "patient_segmentation_kmeans_v1",
        "artifact_location": "dbfs:/mlflow/experiments/3",
        "lifecycle_stage": "active",
        "tags": {"team": "medical_ai", "market": "US"},
        "created_at": datetime(2026, 3, 30, 8, 0, 0, tzinfo=timezone.utc),
    },
]


def _ms_to_datetime(ms: int | None) -> datetime | None:
    """Convert Databricks epoch-ms timestamp to timezone-aware datetime."""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


# ---------------------------------------------------------------------------
# DS-001: List all experiments
# ---------------------------------------------------------------------------
def list_experiments() -> List[ExperimentSummary]:
    """
    Fetch all experiments from Databricks MLflow via the SDK.
    Falls back to mock data if Databricks is unavailable.
    """
    client = get_workspace_client()

    if client is None:
        logger.info("[ExperimentService] Mock mode — returning %d mock experiments", len(MOCK_EXPERIMENTS))
        return [
            ExperimentSummary(
                experiment_id=e["experiment_id"],
                name=e["name"],
                lifecycle_stage=e["lifecycle_stage"],
                created_at=e["created_at"],
            )
            for e in MOCK_EXPERIMENTS
        ]

    try:
        experiments = list(client.experiments.list())
        result = []
        for exp in experiments:
            result.append(
                ExperimentSummary(
                    experiment_id=str(exp.experiment_id),
                    name=exp.name or "",
                    lifecycle_stage=exp.lifecycle_stage or "active",
                    created_at=_ms_to_datetime(exp.creation_time),
                )
            )
        logger.info("[ExperimentService] Fetched %d experiments from Databricks", len(result))
        return result

    except Exception as exc:
        logger.error("[ExperimentService] list_experiments failed: %s — returning mock data", exc)
        return [
            ExperimentSummary(
                experiment_id=e["experiment_id"],
                name=e["name"],
                lifecycle_stage=e["lifecycle_stage"],
                created_at=e["created_at"],
            )
            for e in MOCK_EXPERIMENTS
        ]

def get_experiment_by_id(experiment_id: str) -> ExperimentDetail | None:
    """
    Fetch a single experiment by ID from Databricks MLflow.
    Returns None if not found.
    """
    client = get_workspace_client()

    if client is None:
        logger.info("[ExperimentService] Mock mode — looking up experiment %s", experiment_id)
        mock = next((e for e in MOCK_EXPERIMENTS if e["experiment_id"] == experiment_id), None)
        if mock is None:
            return None
        return ExperimentDetail(
            experiment_id=mock["experiment_id"],
            name=mock["name"],
            artifact_location=mock["artifact_location"],
            lifecycle_stage=mock["lifecycle_stage"],
            tags=mock["tags"],
            created_at=mock["created_at"],
        )

    try:
        exp = client.experiments.get(experiment_id=experiment_id)
        if exp is None or exp.experiment is None:
            return None

        e = exp.experiment
        # Parse tags: SDK returns List[ExperimentTag] → dict
        tags = {}
        if e.tags:
            tags = {tag.key: tag.value for tag in e.tags}

        return ExperimentDetail(
            experiment_id=str(e.experiment_id),
            name=e.name or "",
            artifact_location=e.artifact_location,
            lifecycle_stage=e.lifecycle_stage or "active",
            tags=tags,
            created_at=_ms_to_datetime(e.creation_time),
        )

    except Exception as exc:
        logger.error(
            "[ExperimentService] get_experiment_by_id(%s) failed: %s", experiment_id, exc
        )
        # Try mock fallback
        mock = next((e for e in MOCK_EXPERIMENTS if e["experiment_id"] == experiment_id), None)
        if mock is None:
            return None
        return ExperimentDetail(**mock)
