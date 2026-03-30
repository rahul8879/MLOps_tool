

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas.submission import SubmissionCreate, SubmissionResponse
from services import submission_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a run for admin review (DS-005)",
    response_description="Created submission record with status=PENDING",
)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
):
    """
    Submit an MLflow run for admin review.

    - Validates the request body (run_id, experiment_id, submitted_by).
    - Persists a new submission record in PostgreSQL with status=PENDING.
    - Returns the created submission including its auto-generated ID.

    **Request body example:**
    ```json
    {
        "run_id": "def456uvw",
        "experiment_id": "1",
        "submitted_by": "ds@astrazeneca.com",
        "notes": "Best run with highest AUC-ROC"
    }
    ```
    """
    try:
        return submission_service.create_submission(payload=payload, db=db)
    except Exception as exc:
        logger.exception("[Router:submissions] create_submission failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create submission: {str(exc)}",
        )
