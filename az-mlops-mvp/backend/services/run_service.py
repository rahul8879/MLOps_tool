import math
from datetime import datetime, timezone
from typing import List

from core.databricks_client import get_databricks_client
from schemas.run import RunResponse


def _ms_to_dt(ms):
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _parse_run(run) -> RunResponse:
    info = run.info
    data = run.data

    metrics = {}
    params = {}
    tags = {}

    if data:
        if data.metrics:
            metrics = {
                m.key: (
                    None
                    if m.value is None or math.isnan(m.value) or math.isinf(m.value)
                    else m.value
                )
                for m in data.metrics
            }

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


# ── DS-003: Get all runs for an experiment ──────────────────────
def get_runs_by_experiment(experiment_id: str) -> List[RunResponse]:
    client = get_databricks_client()
    runs = client.experiments.search_runs(
        experiment_ids=[experiment_id]
    )
    return [_parse_run(run) for run in runs]


# ── DS-004: Get metrics for a specific run ──────────────────────
def get_run_by_id(run_id: str) -> RunResponse:
    client = get_databricks_client()
    run = client.experiments.get_run(run_id=run_id)
    return _parse_run(run.run)