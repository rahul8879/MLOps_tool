from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.run_service import get_runs_by_experiment, get_run_by_id
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
    tags=["Runs - Data Scientist"]
)


# DS-003
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
        return JSONResponse(content=make_json_safe([r.model_dump() for r in runs]))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DS-004
@router.get(
    "/{experiment_id}/runs/{run_id}",
    summary="DS-004: Get metrics and params for a specific run"
)
def get_run(experiment_id: str, run_id: str):
    try:
        run = get_run_by_id(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return JSONResponse(content=make_json_safe(run.model_dump()))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))