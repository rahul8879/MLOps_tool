from fastapi import APIRouter, HTTPException
from typing import List
from schemas.experiment import ExperimentResponse
from services.experiment_service import get_all_experiments

router = APIRouter(
    prefix="/experiments",
    tags=["Experiments — Data Scientist"]
)

@router.get(
    "/",
    response_model=List[ExperimentResponse],
    summary="Get all experiments",
)
def list_experiments():
    try:
        return get_all_experiments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))