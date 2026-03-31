from pydantic import BaseModel
from typing import Optional, Dict, Any
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

    # Any type — no strict validation
    metrics: Optional[Dict[str, Any]] = {}
    params: Optional[Dict[str, Any]] = {}
    tags: Optional[Dict[str, Any]] = {}

    class Config:
        from_attributes = True