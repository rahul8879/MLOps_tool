from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas.experiment import ExperimentResponse
from services.experiment_service import (
    get_all_experiments,
    get_experiment_by_id,
    search_experiments_by_name
)

router = APIRouter(
    prefix="/experiments",
    tags=["Experiments — Data Scientist"]
)


@router.get(
    "/",
    response_model=List[ExperimentResponse],
    summary="Get all experiments"
)
def list_experiments():
    try:
        return get_all_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    response_model=List[ExperimentResponse],
    summary="Search experiments by name"
)
def search_experiments(name: str = Query(..., description="Partial experiment name")):
    try:
        return search_experiments_by_name(name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{experiment_id}",
    response_model=ExperimentResponse,
    summary="DS-002: Get experiment by ID"
)
def get_experiment(experiment_id: str):
    try:
        result = get_experiment_by_id(experiment_id)
        if not result:
            raise HTTPException(status_code=404, detail="Experiment not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))