"""
db/models.py
============
SQLAlchemy ORM models for all five tables:

  1. experiments   — synced from Databricks MLflow
  2. runs          — synced from Databricks MLflow
  3. metrics       — per-run metric values
  4. params        — per-run hyperparameter values
  5. submissions   — DS → Admin review workflow
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Experiments
# ---------------------------------------------------------------------------
class Experiment(Base):
    __tablename__ = "experiments"

    experiment_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    artifact_location = Column(String, nullable=True)
    lifecycle_stage = Column(String, default="active", nullable=False)
    tags = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    synced_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    runs = relationship("Run", back_populates="experiment", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="experiment")

    def __repr__(self):
        return f"<Experiment id={self.experiment_id} name={self.name}>"


# ---------------------------------------------------------------------------
# 2. Runs
# ---------------------------------------------------------------------------
class Run(Base):
    __tablename__ = "runs"

    run_id = Column(String, primary_key=True, index=True)
    experiment_id = Column(
        String, ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String, default="RUNNING", nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    # Relationships
    experiment = relationship("Experiment", back_populates="runs")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")
    params = relationship("Param", back_populates="run", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="run")

    def __repr__(self):
        return f"<Run id={self.run_id} status={self.status}>"


# ---------------------------------------------------------------------------
# 3. Metrics
# ---------------------------------------------------------------------------
class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String, ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False, index=True
    )
    key = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(BigInteger, nullable=True)

    # Relationship
    run = relationship("Run", back_populates="metrics")

    def __repr__(self):
        return f"<Metric run={self.run_id} {self.key}={self.value}>"


# ---------------------------------------------------------------------------
# 4. Params
# ---------------------------------------------------------------------------
class Param(Base):
    __tablename__ = "params"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String, ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False, index=True
    )
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)

    # Relationship
    run = relationship("Run", back_populates="params")

    def __repr__(self):
        return f"<Param run={self.run_id} {self.key}={self.value}>"


# ---------------------------------------------------------------------------
# 5. Submissions
# ---------------------------------------------------------------------------
class Submission(Base):
    __tablename__ = "submissions"

    submission_id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(
        String, ForeignKey("runs.run_id", ondelete="SET NULL"), nullable=True, index=True
    )
    experiment_id = Column(
        String, ForeignKey("experiments.experiment_id", ondelete="SET NULL"), nullable=True, index=True
    )
    submitted_by = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False)  # PENDING | APPROVED | REJECTED
    notes = Column(Text, nullable=True)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    # Relationships
    run = relationship("Run", back_populates="submissions")
    experiment = relationship("Experiment", back_populates="submissions")

    def __repr__(self):
        return f"<Submission id={self.submission_id} run={self.run_id} status={self.status}>"
