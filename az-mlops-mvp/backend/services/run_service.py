from core.databricks_client import get_databricks_client
from schemas.run import RunResponse
from typing import List
from datetime import datetime, timezone


def _ms_to_dt(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None


def _parse_run(run) -> RunResponse:
    info = run.info   # RunInfo object
    data = run.data   # RunData object

    metrics = {}
    params = {}
    tags = {}

    if data:
        if data.metrics:
            metrics = {m.key: m.value for m in data.metrics}
        if data.params:
            params = {p.key: p.value for p in data.params}
        if data.tags:
            tags = {t.key: t.value for t in data.tags}

    return RunResponse(
        run_id=info.run_id,
        run_name=info.run_name if hasattr(info, 'run_name') else None,
        experiment_id=info.experiment_id,
        status=info.status.value if info.status else None,
        lifecycle_stage=info.lifecycle_stage,
        start_time=_ms_to_dt(info.start_time),
        end_time=_ms_to_dt(info.end_time),
        artifact_uri=info.artifact_uri,
        user_id=info.user_id,
        metrics=metrics,
        params=params,
        tags=tags,
    )


def get_runs_by_experiment(experiment_id: str) -> List[RunResponse]:
    """DS-003 — Get all runs for a given experiment ID"""
    client = get_databricks_client()

    # search_runs returns SearchRunsResponse — access .runs
    response = client.experiments.search_runs(
        experiment_ids=[experiment_id]
    )

    runs = response.runs if response.runs else []
    return [_parse_run(r) for r in runs]