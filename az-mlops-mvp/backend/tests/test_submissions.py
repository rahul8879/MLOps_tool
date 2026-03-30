"""
tests/test_submissions.py
==========================
Tests for Submission endpoints (DS-005).

Uses an in-memory SQLite database so tests are fully self-contained
and don't need a running PostgreSQL instance.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

# Use SQLite in-memory for tests (avoids needing PostgreSQL)
TEST_DATABASE_URL = "sqlite:///./test_submissions.db"

# Patch config DATABASE_URL before importing the app
with patch("core.config.settings") as mock_settings:
    mock_settings.APP_ENV = "testing"
    mock_settings.DATABRICKS_HOST = None
    mock_settings.DATABRICKS_TOKEN = None
    mock_settings.use_mock_data = True
    mock_settings.is_production = False
    mock_settings.CORS_ORIGINS = ["*"]
    mock_settings.DATABASE_URL = TEST_DATABASE_URL
    mock_settings.DATABRICKS_MODEL_NAME = "drug_efficacy_prod"
    mock_settings.DATABRICKS_DEPLOYED_MODEL_VERSION = "latest"

from db.database import Base, get_db
from main import app

# --- Set up in-memory SQLite engine ---
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Create all tables before tests and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# DS-005: POST /submissions
# ---------------------------------------------------------------------------
class TestCreateSubmission:
    def test_returns_201_on_success(self, client):
        payload = {
            "run_id": "def456uvw",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
            "notes": "Best run with highest AUC-ROC",
        }
        response = client.post("/submissions", json=payload)
        assert response.status_code == 201

    def test_response_has_submission_id(self, client):
        payload = {
            "run_id": "abc123xyz",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
        }
        response = client.post("/submissions", json=payload)
        data = response.json()
        assert "submission_id" in data
        assert isinstance(data["submission_id"], int)
        assert data["submission_id"] > 0

    def test_status_is_pending(self, client):
        payload = {
            "run_id": "abc123xyz",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
        }
        response = client.post("/submissions", json=payload)
        assert response.json()["status"] == "PENDING"

    def test_response_mirrors_request_fields(self, client):
        payload = {
            "run_id": "ghi789rst",
            "experiment_id": "2",
            "submitted_by": "analyst@astrazeneca.com",
            "notes": "Test note",
        }
        response = client.post("/submissions", json=payload)
        data = response.json()
        assert data["run_id"] == payload["run_id"]
        assert data["submitted_by"] == payload["submitted_by"]
        assert data["notes"] == payload["notes"]

    def test_submission_ids_are_unique(self, client):
        payload = {
            "run_id": "def456uvw",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
        }
        r1 = client.post("/submissions", json=payload)
        r2 = client.post("/submissions", json=payload)
        assert r1.json()["submission_id"] != r2.json()["submission_id"]

    def test_created_at_is_present(self, client):
        payload = {
            "run_id": "abc123xyz",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
        }
        response = client.post("/submissions", json=payload)
        assert "created_at" in response.json()
        assert response.json()["created_at"] is not None

    def test_missing_run_id_returns_422(self, client):
        payload = {
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
        }
        response = client.post("/submissions", json=payload)
        assert response.status_code == 422

    def test_missing_submitted_by_returns_422(self, client):
        payload = {
            "run_id": "abc123xyz",
            "experiment_id": "1",
        }
        response = client.post("/submissions", json=payload)
        assert response.status_code == 422

    def test_notes_is_optional(self, client):
        payload = {
            "run_id": "abc123xyz",
            "experiment_id": "1",
            "submitted_by": "ds@astrazeneca.com",
            # no notes field
        }
        response = client.post("/submissions", json=payload)
        assert response.status_code == 201

    def test_empty_body_returns_422(self, client):
        response = client.post("/submissions", json={})
        assert response.status_code == 422
