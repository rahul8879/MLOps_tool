from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from schemas.run import RunResponse
from services.run_service import get_runs_by_experiment
import math


def make_json_safe(obj):
    """
    Recursively clean any object before JSON response.
    Handles nan, inf, nested dicts, lists.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
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
    summary="DS-003: Get all runs for an experiment"
)
def list_runs(experiment_id: str):
    try:
        runs = get_runs_by_experiment(experiment_id)
        # Convert to dict first, then sanitize
        safe_data = make_json_safe([r.model_dump() for r in runs])
        return JSONResponse(content=safe_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
