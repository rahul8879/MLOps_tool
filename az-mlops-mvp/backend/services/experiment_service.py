from core.databricks_client import get_databricks_client
from schemas.experiment import ExperimentResponse
from typing import List, Optional
from datetime import datetime, timezone


def _parse_experiment(exp) -> ExperimentResponse:
    """
    Common parser — reused by get_all, get_by_id, search_by_name
    """
    tags = {}
    if exp.tags:
        tags = {t.key: t.value for t in exp.tags}

    def ms_to_dt(ms):
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None

    return ExperimentResponse(
        experiment_id=exp.experiment_id,
        name=exp.name,
        artifact_location=exp.artifact_location,
        lifecycle_stage=exp.lifecycle_stage,
        creation_time=ms_to_dt(exp.creation_time),
        last_update_time=ms_to_dt(exp.last_update_time),
        owner_email=tags.get("mlflow.ownerEmail"),
        experiment_kind=tags.get("mlflow.experimentKind"),
        tags=tags,
    )


def get_all_experiments() -> List[ExperimentResponse]:
    client = get_databricks_client()
    return [_parse_experiment(e) for e in client.experiments.search_experiments()]


def get_experiment_by_id(experiment_id: str) -> Optional[ExperimentResponse]:
    """ Get experiment by ID"""
    client = get_databricks_client()
    exp = client.experiments.get_experiment(experiment_id=experiment_id)
    if not exp or not exp.experiment:
        return None
    return _parse_experiment(exp.experiment)


def search_experiments_by_name(name: str) -> List[ExperimentResponse]:
    """Search experiments by name (partial match)"""
    client = get_databricks_client()
    experiments = client.experiments.search_experiments(
        filter=f"name LIKE '%{name}%'"
    )
    return [_parse_experiment(e) for e in experiments]