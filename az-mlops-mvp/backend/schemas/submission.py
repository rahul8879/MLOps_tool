

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SubmissionCreate(BaseModel):
    """
    Data Scientist submits a run for admin review.
    """

    run_id: str = Field(..., description="The MLflow run ID to submit for review")
    experiment_id: str = Field(..., description="The parent experiment ID")
    submitted_by: str = Field(
        ...,
        description="Email of the submitting data scientist",
        examples=["ds@gmail.com"],
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes / justification for this submission",
        max_length=2000,
    )


class SubmissionResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    submission_id: int = Field(..., description="Auto-generated submission ID")
    run_id: str
    experiment_id: Optional[str] = None
    submitted_by: str
    status: str = Field(..., description="PENDING | APPROVED | REJECTED")
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
