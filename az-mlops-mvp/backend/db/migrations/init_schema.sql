-- ============================================================
-- AstraZeneca MLOps MVP — Initial Schema
-- Reference SQL (Alembic manages actual migrations)
-- Run manually for a clean bootstrap or reference only.
-- ============================================================

-- Enable JSONB support (requires PostgreSQL 9.4+)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------
-- 1. experiments
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id       VARCHAR         PRIMARY KEY,
    name                VARCHAR         NOT NULL,
    artifact_location   VARCHAR,
    lifecycle_stage     VARCHAR         NOT NULL DEFAULT 'active',
    tags                JSONB           DEFAULT '{}',
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    synced_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE experiments IS 'MLflow experiments synced from Azure Databricks workspace.';
COMMENT ON COLUMN experiments.tags IS 'Arbitrary key-value metadata stored as JSONB (team, brand, market, etc.).';

CREATE INDEX IF NOT EXISTS idx_experiments_lifecycle ON experiments(lifecycle_stage);
CREATE INDEX IF NOT EXISTS idx_experiments_name      ON experiments(name);

-- ----------------------------------------------------------------
-- 2. runs
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS runs (
    run_id          VARCHAR         PRIMARY KEY,
    experiment_id   VARCHAR         NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    status          VARCHAR         NOT NULL DEFAULT 'RUNNING',
    start_time      TIMESTAMPTZ,
    end_time        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE runs IS 'MLflow runs for each experiment, synced from Databricks.';
COMMENT ON COLUMN runs.status IS 'RUNNING | SCHEDULED | FINISHED | FAILED | KILLED';

CREATE INDEX IF NOT EXISTS idx_runs_experiment_id ON runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_runs_status        ON runs(status);

-- ----------------------------------------------------------------
-- 3. metrics
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrics (
    id          SERIAL          PRIMARY KEY,
    run_id      VARCHAR         NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    key         VARCHAR         NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    timestamp   BIGINT
);

COMMENT ON TABLE metrics IS 'Per-run metric values (accuracy, f1_score, rmse, etc.).';

CREATE INDEX IF NOT EXISTS idx_metrics_run_id ON metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_metrics_key    ON metrics(key);

-- ----------------------------------------------------------------
-- 4. params
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS params (
    id      SERIAL      PRIMARY KEY,
    run_id  VARCHAR     NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    key     VARCHAR     NOT NULL,
    value   TEXT
);

COMMENT ON TABLE params IS 'Per-run hyperparameter values (n_estimators, max_depth, etc.).';

CREATE INDEX IF NOT EXISTS idx_params_run_id ON params(run_id);

-- ----------------------------------------------------------------
-- 5. submissions
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS submissions (
    submission_id   SERIAL      PRIMARY KEY,
    run_id          VARCHAR     REFERENCES runs(run_id) ON DELETE SET NULL,
    experiment_id   VARCHAR     REFERENCES experiments(experiment_id) ON DELETE SET NULL,
    submitted_by    VARCHAR     NOT NULL,
    status          VARCHAR     NOT NULL DEFAULT 'PENDING',
    notes           TEXT,
    assigned_to     VARCHAR,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE submissions IS 'Data scientist run submissions awaiting admin review.';
COMMENT ON COLUMN submissions.status IS 'PENDING | APPROVED | REJECTED';

CREATE INDEX IF NOT EXISTS idx_submissions_run_id        ON submissions(run_id);
CREATE INDEX IF NOT EXISTS idx_submissions_experiment_id ON submissions(experiment_id);
CREATE INDEX IF NOT EXISTS idx_submissions_status        ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_by  ON submissions(submitted_by);

-- ----------------------------------------------------------------
-- Trigger: auto-update submissions.updated_at
-- ----------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_submissions_updated_at ON submissions;
CREATE TRIGGER trg_submissions_updated_at
    BEFORE UPDATE ON submissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
