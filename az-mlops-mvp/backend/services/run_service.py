import math
from core.databricks_client import get_databricks_client
from schemas.run import RunResponse
from typing import List, Optional, Any
from datetime import datetime, timezone


def _ms_to_dt(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc) if ms else None


def _clean_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def _parse_run(run) -> RunResponse:
    info = run.info
    data = run.data

    metrics = {}
    params = {}
    tags = {}

    if data:
        if data.metrics:
            metrics = {m.key: _clean_value(m.value) for m in data.metrics}
        if data.params:
            params = {p.key: _clean_value(p.value) for p in data.params}
        if data.tags:
            tags = {t.key: _clean_value(t.value) for t in data.tags}

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


# DS-003 — Get runs for experiment (PERFORMANCE FIX)
def get_runs_by_experiment(
    experiment_id: str,
    max_results: int = 20
) -> List[RunResponse]:
    client = get_databricks_client()

    # Pass max_results directly to SDK — avoids full pagination
    runs = client.experiments.search_runs(
        experiment_ids=[experiment_id],
        filter="attributes.status = 'FINISHED'",
        max_results=max_results,   # SDK will stop after this
    )

    # list() only after max_results is set — not before
    return [_parse_run(r) for r in runs]


# DS-004 — Get single run metrics (NEW)
def get_run_by_id(run_id: str) -> Optional[RunResponse]:
    """
    Uses get_run() — fetches ONE run directly by ID.
    Much faster than search_runs for single run lookup.
    SDK: client.experiments.get_run(run_id)
    Returns: GetRunResponse.run
    """
    client = get_databricks_client()
    response = client.experiments.get_run(run_id=run_id)

    if not response or not response.run:
        return None

    return _parse_run(response.run)