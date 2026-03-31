from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    artifact_location: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None

    # Extracted from tags — useful for DS
    owner_email: Optional[str] = None
    experiment_kind: Optional[str] = None

    # Raw tags still available
    tags: Optional[Dict[str, str]] = {}

    class Config:
        from_attributes = True