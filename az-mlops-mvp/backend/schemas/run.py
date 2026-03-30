
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

class RunBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run_id: str = Field(..., description="Databricks MLflow run ID")
    metrics: Dict[str, float] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)

class RunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    run_id: str
    experiment_id: str
    status: str = Field(..., description="RUNNING | FINISHED | FAILED | KILLED")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    params: Dict[str, str] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)

class RunMetricsResponse(BaseModel):
    """Full metrics, params, and tags for a single run."""

    run_id: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    tags: Dict[str, Any] = Field(default_factory=dict)

class RunCompareItem(BaseModel):
    run_id: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)


class ComparisonWinner(BaseModel):
    run_id: str
    reason: str


class RunCompareResponse(BaseModel):
    """Side-by-side comparison of multiple runs, with a winner recommendation."""

    runs: List[RunCompareItem]
    winner: Optional[ComparisonWinner] = None

class CandidateRunInfo(BaseModel):
    run_id: str
    metrics: Dict[str, float] = Field(default_factory=dict)


class DeployedModelInfo(BaseModel):
    model_name: str
    version: str
    metrics: Dict[str, float] = Field(default_factory=dict)


class ComparisonResult(BaseModel):
    accuracy_delta: Optional[float] = None
    recommendation: str = Field(..., description="PROMOTE | HOLD | REJECT")
    reason: str


class CompareDeployedResponse(BaseModel):

    candidate_run: CandidateRunInfo
    deployed_model: DeployedModelInfo
    comparison: ComparisonResult
