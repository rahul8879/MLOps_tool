from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class RunResponse(BaseModel):
    run_id: str
    run_name: Optional[str] = None
    experiment_id: str
    status: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    artifact_uri: Optional[str] = None
    user_id: Optional[str] = None

    # From RunData
    metrics: Optional[Dict[str, float]] = {}
    params: Optional[Dict[str, str]] = {}
    tags: Optional[Dict[str, str]] = {}

    class Config:
        from_attributes = True