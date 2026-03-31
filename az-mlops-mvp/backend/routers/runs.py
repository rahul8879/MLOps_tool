from fastapi import APIRouter, HTTPException
from typing import List
from schemas.run import RunResponse
from services.run_service import get_runs_by_experiment

router = APIRouter(
    prefix="/experiments",
    tags=["Runs — Data Scientist"]
)


@router.get(
    "/{experiment_id}/runs",
    response_model=List[RunResponse],
    summary="Get all runs for an experiment"
)
def list_runs(experiment_id: str):
    try:
        return get_runs_by_experiment(experiment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))