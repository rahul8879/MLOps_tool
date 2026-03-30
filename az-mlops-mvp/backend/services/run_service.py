

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.databricks_client import get_workspace_client
from core.config import settings
from schemas.run import (
    CandidateRunInfo,
    CompareDeployedResponse,
    ComparisonResult,
    ComparisonWinner,
    DeployedModelInfo,
    RunCompareItem,
    RunCompareResponse,
    RunMetricsResponse,
    RunSummary,
)

logger = logging.getLogger(__name__)

MOCK_RUNS = {
    "1": [
        {
            "run_id": "abc123xyz",
            "experiment_id": "1",
            "status": "FINISHED",
            "start_time": datetime(2026, 3, 28, 10, 5, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 3, 28, 10, 45, 0, tzinfo=timezone.utc),
            "params": {"n_estimators": "200", "max_depth": "6", "learning_rate": "0.1"},
            "metrics": {"accuracy": 0.91, "f1_score": 0.88, "rmse": 0.12, "auc_roc": 0.94},
            "tags": {"mlflow.user": "ds@test.com"},
        },
        {
            "run_id": "def456uvw",
            "experiment_id": "1",
            "status": "FINISHED",
            "start_time": datetime(2026, 3, 29, 9, 0, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 3, 29, 9, 55, 0, tzinfo=timezone.utc),
            "params": {"n_estimators": "300", "max_depth": "8", "learning_rate": "0.05"},
            "metrics": {"accuracy": 0.93, "f1_score": 0.91, "rmse": 0.09, "auc_roc": 0.96},
            "tags": {"mlflow.user": "ds2@astrazeneca.com"},
        },
    ],
    "2": [
        {
            "run_id": "ghi789rst",
            "experiment_id": "2",
            "status": "FINISHED",
            "start_time": datetime(2026, 3, 30, 8, 0, 0, tzinfo=timezone.utc),
            "end_time": datetime(2026, 3, 30, 8, 30, 0, tzinfo=timezone.utc),
            "params": {"n_estimators": "500", "num_leaves": "31"},
            "metrics": {"accuracy": 0.92, "f1_score": 0.90, "rmse": 0.10},
            "tags": {"mlflow.user": "ds@astrazeneca.com"},
        }
    ],
}

# Flat map run_id → run data for quick lookup
MOCK_RUNS_BY_ID: Dict = {
    run["run_id"]: run
    for runs in MOCK_RUNS.values()
    for run in runs
}

# Mock deployed model
MOCK_DEPLOYED_MODEL = {
    "model_name": "drug_efficacy_prod",
    "version": "3",
    "metrics": {"accuracy": 0.89, "f1_score": 0.86, "rmse": 0.14, "auc_roc": 0.92},
}


def _ms_to_datetime(ms) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)


def get_runs_for_experiment(experiment_id: str) -> List[RunSummary]:
    """
    Fetch all runs for a given experiment from Databricks.
    """
    client = get_workspace_client()

    if client is None:
        logger.info("[RunService] Mock mode — fetching runs for experiment %s", experiment_id)
        mock_runs = MOCK_RUNS.get(experiment_id, [])
        return [
            RunSummary(
                run_id=r["run_id"],
                experiment_id=r["experiment_id"],
                status=r["status"],
                start_time=r["start_time"],
                end_time=r["end_time"],
                params=r["params"],
                metrics=r["metrics"],
            )
            for r in mock_runs
        ]

    try:
        from databricks.sdk.service.ml import SearchRunsRequest

        runs_page = client.experiments.search_runs(
            experiment_ids=[experiment_id],
            max_results=200,
        )

        result = []
        for run in (runs_page or []):
            info = run.info
            data = run.data

            metrics = {}
            if data and data.metrics:
                metrics = {m.key: m.value for m in data.metrics}

            params = {}
            if data and data.params:
                params = {p.key: p.value for p in data.params}

            result.append(
                RunSummary(
                    run_id=info.run_id,
                    experiment_id=info.experiment_id,
                    status=info.status.value if info.status else "UNKNOWN",
                    start_time=_ms_to_datetime(info.start_time),
                    end_time=_ms_to_datetime(info.end_time),
                    params=params,
                    metrics=metrics,
                )
            )
        return result

    except Exception as exc:
        logger.error("[RunService] get_runs_for_experiment(%s) failed: %s — mock fallback", experiment_id, exc)
        mock_runs = MOCK_RUNS.get(experiment_id, [])
        return [
            RunSummary(
                run_id=r["run_id"],
                experiment_id=r["experiment_id"],
                status=r["status"],
                start_time=r["start_time"],
                end_time=r["end_time"],
                params=r["params"],
                metrics=r["metrics"],
            )
            for r in mock_runs
        ]


def get_run_metrics(run_id: str) -> Optional[RunMetricsResponse]:
    """
    Fetch metrics, params, and tags for a single run.
    Returns None if run not found.
    """
    client = get_workspace_client()

    if client is None:
        logger.info("[RunService] Mock mode — fetching metrics for run %s", run_id)
        r = MOCK_RUNS_BY_ID.get(run_id)
        if r is None:
            return None
        return RunMetricsResponse(
            run_id=r["run_id"],
            metrics=r["metrics"],
            params=r["params"],
            tags=r.get("tags", {}),
        )

    try:
        run = client.experiments.get_run(run_id=run_id)
        if run is None or run.run is None:
            return None

        data = run.run.data
        metrics = {m.key: m.value for m in (data.metrics or [])}
        params = {p.key: p.value for p in (data.params or [])}
        tags = {t.key: t.value for t in (data.tags or [])}

        return RunMetricsResponse(run_id=run_id, metrics=metrics, params=params, tags=tags)

    except Exception as exc:
        logger.error("[RunService] get_run_metrics(%s) failed: %s — mock fallback", run_id, exc)
        r = MOCK_RUNS_BY_ID.get(run_id)
        if r is None:
            return None
        return RunMetricsResponse(
            run_id=r["run_id"],
            metrics=r["metrics"],
            params=r["params"],
            tags=r.get("tags", {}),
        )

def _determine_winner(runs: List[RunCompareItem]) -> Optional[ComparisonWinner]:
    """
    Simple heuristic: highest accuracy wins.
    If accuracy is tied, pick the one with the lowest RMSE.
    """
    if len(runs) < 2:
        return None

    scored = []
    for r in runs:
        acc = r.metrics.get("accuracy", 0.0)
        rmse = r.metrics.get("rmse", float("inf"))
        scored.append((r.run_id, acc, rmse))

    scored.sort(key=lambda x: (-x[1], x[2]))  # desc accuracy, asc rmse
    best_id, best_acc, best_rmse = scored[0]
    second_id, second_acc, second_rmse = scored[1]

    if best_acc > second_acc and best_rmse < second_rmse:
        reason = "Higher accuracy and lower RMSE"
    elif best_acc > second_acc:
        reason = "Higher accuracy"
    elif best_rmse < second_rmse:
        reason = "Lower RMSE"
    else:
        reason = "Best overall metric profile"

    return ComparisonWinner(run_id=best_id, reason=reason)


def compare_runs(run_ids: List[str]) -> Optional[RunCompareResponse]:
    """
    Fetch multiple runs and compare them side-by-side.
    Returns None if no runs found.
    """
    client = get_workspace_client()
    items: List[RunCompareItem] = []

    for run_id in run_ids:
        run_id = run_id.strip()
        if client is None:
            r = MOCK_RUNS_BY_ID.get(run_id)
            if r:
                items.append(
                    RunCompareItem(
                        run_id=r["run_id"],
                        metrics=r["metrics"],
                        params=r["params"],
                    )
                )
        else:
            try:
                run = client.experiments.get_run(run_id=run_id)
                if run and run.run:
                    data = run.run.data
                    metrics = {m.key: m.value for m in (data.metrics or [])}
                    params = {p.key: p.value for p in (data.params or [])}
                    items.append(RunCompareItem(run_id=run_id, metrics=metrics, params=params))
            except Exception as exc:
                logger.warning("[RunService] compare_runs: failed to fetch %s: %s", run_id, exc)
                # Try mock
                r = MOCK_RUNS_BY_ID.get(run_id)
                if r:
                    items.append(
                        RunCompareItem(run_id=r["run_id"], metrics=r["metrics"], params=r["params"])
                    )

    if not items:
        return None

    winner = _determine_winner(items)
    return RunCompareResponse(runs=items, winner=winner)


# ---------------------------------------------------------------------------
# DS-007: Compare run vs deployed model
# ---------------------------------------------------------------------------
def compare_run_vs_deployed(run_id: str) -> Optional[CompareDeployedResponse]:
    """
    Compare a candidate run against the currently deployed model version.
    Deployed model metrics are fetched via Databricks Model Registry.
    """
    client = get_workspace_client()

    # --- Fetch candidate run ---
    if client is None:
        candidate_data = MOCK_RUNS_BY_ID.get(run_id)
        if candidate_data is None:
            return None
        candidate_metrics = candidate_data["metrics"]
        deployed = MOCK_DEPLOYED_MODEL
    else:
        try:
            run = client.experiments.get_run(run_id=run_id)
            if run is None or run.run is None:
                return None
            data = run.run.data
            candidate_metrics = {m.key: m.value for m in (data.metrics or [])}
        except Exception as exc:
            logger.error("[RunService] compare_run_vs_deployed — get_run failed: %s", exc)
            r = MOCK_RUNS_BY_ID.get(run_id)
            if r is None:
                return None
            candidate_metrics = r["metrics"]

        # --- Fetch deployed model metrics from Model Registry ---
        try:
            model_name = settings.DATABRICKS_MODEL_NAME
            versions = list(
                client.model_registry.get_latest_versions(
                    name=model_name, stages=["Production"]
                )
            )
            if not versions:
                raise ValueError(f"No Production version found for model '{model_name}'")

            latest_version = versions[0]
            version_str = str(latest_version.version)

            # Fetch run linked to this model version
            source_run_id = latest_version.run_id
            if source_run_id:
                dep_run = client.experiments.get_run(run_id=source_run_id)
                dep_data = dep_run.run.data
                dep_metrics = {m.key: m.value for m in (dep_data.metrics or [])}
            else:
                dep_metrics = {}

            deployed = {
                "model_name": model_name,
                "version": version_str,
                "metrics": dep_metrics,
            }
        except Exception as exc:
            logger.warning(
                "[RunService] Could not fetch deployed model metrics: %s — using mock", exc
            )
            deployed = MOCK_DEPLOYED_MODEL

    # --- Build comparison ---
    cand_acc = candidate_metrics.get("accuracy", 0.0)
    dep_acc = deployed["metrics"].get("accuracy", 0.0)
    acc_delta = round(cand_acc - dep_acc, 4)

    if acc_delta > 0.01:
        recommendation = "PROMOTE"
        reason = "Candidate outperforms on all metrics"
    elif acc_delta < -0.01:
        recommendation = "REJECT"
        reason = "Candidate underperforms the deployed model"
    else:
        recommendation = "HOLD"
        reason = "Marginal difference — further evaluation recommended"

    return CompareDeployedResponse(
        candidate_run=CandidateRunInfo(run_id=run_id, metrics=candidate_metrics),
        deployed_model=DeployedModelInfo(
            model_name=deployed["model_name"],
            version=str(deployed["version"]),
            metrics=deployed["metrics"],
        ),
        comparison=ComparisonResult(
            accuracy_delta=acc_delta,
            recommendation=recommendation,
            reason=reason,
        ),
    )
