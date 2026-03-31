from core.databricks_client import get_databricks_client
from schemas.experiment import ExperimentResponse
from typing import List
from datetime import datetime, timezone


def get_all_experiments() -> List[ExperimentResponse]:
    client = get_databricks_client()
    experiments = client.experiments.search_experiments()

    result = []
    for exp in experiments:
        # tags: List[ExperimentTag] → {key: value}
        tags = {}
        if exp.tags:
            tags = {t.key: t.value for t in exp.tags}

        # creation_time: int (ms) → datetime
        created_at = None
        if exp.creation_time:
            created_at = datetime.fromtimestamp(
                exp.creation_time / 1000, tz=timezone.utc
            )

        result.append(ExperimentResponse(
            experiment_id=exp.experiment_id,
            name=exp.name,
            artifact_location=exp.artifact_location,
            lifecycle_stage=exp.lifecycle_stage,  # already str!
            tags=tags,
            creation_time=created_at,
        ))
    return result