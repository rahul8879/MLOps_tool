
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExperimentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    experiment_id: str = Field(..., description="Databricks MLflow experiment ID")
    name: str = Field(..., description="Experiment name")
    lifecycle_stage: str = Field(..., description="active | deleted")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp (UTC)")


class ExperimentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    experiment_id: str = Field(..., description="Databricks MLflow experiment ID")
    name: str = Field(..., description="Experiment name")
    artifact_location: Optional[str] = Field(
        None, description="DBFS artifact root, e.g. dbfs:/mlflow/experiments/1"
    )
    lifecycle_stage: str = Field(..., description="active | deleted")
    tags: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Arbitrary metadata (team, brand, market, etc.)",
    )
    created_at: Optional[datetime] = Field(None, description="Creation timestamp (UTC)")


class ExperimentsListResponse(BaseModel):
    experiments: List[ExperimentSummary]
    total: int = Field(..., description="Total number of experiments returned")
