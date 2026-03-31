from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class ExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    artifact_location: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    tags: Optional[Dict[str, str]] = {}
    creation_time: Optional[datetime] = None

    class Config:
        from_attributes = True