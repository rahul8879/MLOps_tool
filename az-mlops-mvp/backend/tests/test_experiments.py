"""
tests/test_experiments.py
==========================
Tests for Experiment endpoints (DS-001, DS-002).

All tests run against mock data — no real Databricks connection needed.
The Databricks client singleton is patched to return None (mock mode).
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Patch the singleton BEFORE importing the app so mock mode is forced
with patch("core.databricks_client.get_workspace_client", return_value=None):
    from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def force_mock_mode():
    """Ensure every test runs with the Databricks client returning None."""
    with patch("services.experiment_service.get_workspace_client", return_value=None):
        yield


# ---------------------------------------------------------------------------
# DS-001: GET /experiments
# ---------------------------------------------------------------------------
class TestListExperiments:
    def test_returns_200(self):
        response = client.get("/experiments")
        assert response.status_code == 200

    def test_returns_list(self):
        response = client.get("/experiments")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_experiment_has_required_fields(self):
        response = client.get("/experiments")
        experiment = response.json()[0]
        assert "experiment_id" in experiment
        assert "name" in experiment
        assert "lifecycle_stage" in experiment

    def test_experiment_ids_are_strings(self):
        response = client.get("/experiments")
        for exp in response.json():
            assert isinstance(exp["experiment_id"], str)

    def test_mock_contains_known_experiment(self):
        response = client.get("/experiments")
        names = [e["name"] for e in response.json()]
        assert "drug_efficacy_xgboost_v1" in names


# ---------------------------------------------------------------------------
# DS-002: GET /experiments/{experiment_id}
# ---------------------------------------------------------------------------
class TestGetExperiment:
    def test_returns_200_for_valid_id(self):
        response = client.get("/experiments/1")
        assert response.status_code == 200

    def test_returns_full_detail(self):
        response = client.get("/experiments/1")
        data = response.json()
        assert data["experiment_id"] == "1"
        assert data["name"] == "drug_efficacy_xgboost_v1"
        assert "artifact_location" in data
        assert "tags" in data
        assert "lifecycle_stage" in data

    def test_tags_contain_expected_keys(self):
        response = client.get("/experiments/1")
        tags = response.json()["tags"]
        assert "team" in tags
        assert "brand" in tags

    def test_returns_404_for_unknown_id(self):
        response = client.get("/experiments/999999")
        assert response.status_code == 404

    def test_404_error_message(self):
        response = client.get("/experiments/does_not_exist")
        assert "not found" in response.json()["detail"].lower()

    def test_second_experiment_exists(self):
        response = client.get("/experiments/2")
        assert response.status_code == 200
        assert response.json()["name"] == "drug_efficacy_lightgbm_v2"


# ---------------------------------------------------------------------------
# Health check (sanity)
# ---------------------------------------------------------------------------
class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_reports_mock_mode(self):
        response = client.get("/health")
        # In test env there are no real creds, so mock_mode should be True
        assert response.json()["mock_mode"] is True
