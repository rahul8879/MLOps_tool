from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.run_service import get_runs_by_experiment
import math
from datetime import datetime


def make_json_safe(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(i) for i in obj]
    return obj


router = APIRouter(
    prefix="/experiments",
    tags=["Runs — Data Scientist"]
)


@router.get(
    "/{experiment_id}/runs",
    summary="DS-003: Get FINISHED runs for an experiment"
)
def list_runs(
    experiment_id: str,
    max_results: int = Query(default=20, description="Max runs to fetch", le=200)
):
    try:
        runs = get_runs_by_experiment(experiment_id, max_results=max_results)
        safe_data = make_json_safe([r.model_dump() for r in runs])
        return JSONResponse(content=safe_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))