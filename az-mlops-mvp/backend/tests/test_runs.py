"""
tests/test_runs.py
==================
Tests for Run endpoints (DS-003, DS-004, DS-006, DS-007).

All tests run in mock mode — no real Databricks connection needed.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

with patch("core.databricks_client.get_workspace_client", return_value=None):
    from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def force_mock_mode():
    with patch("services.run_service.get_workspace_client", return_value=None):
        yield


# ---------------------------------------------------------------------------
# DS-003: GET /experiments/{experiment_id}/runs
# ---------------------------------------------------------------------------
class TestGetRunsForExperiment:
    def test_returns_200_for_valid_experiment(self):
        response = client.get("/experiments/1/runs")
        assert response.status_code == 200

    def test_returns_list_of_runs(self):
        response = client.get("/experiments/1/runs")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_run_has_required_fields(self):
        response = client.get("/experiments/1/runs")
        run = response.json()[0]
        for field in ("run_id", "experiment_id", "status", "params", "metrics"):
            assert field in run, f"Missing field: {field}"

    def test_run_metrics_are_floats(self):
        response = client.get("/experiments/1/runs")
        for run in response.json():
            for val in run["metrics"].values():
                assert isinstance(val, (int, float))

    def test_returns_404_for_unknown_experiment(self):
        response = client.get("/experiments/999999/runs")
        assert response.status_code == 404

    def test_experiment_2_runs(self):
        response = client.get("/experiments/2/runs")
        assert response.status_code == 200
        assert len(response.json()) >= 1


# ---------------------------------------------------------------------------
# DS-004: GET /runs/{run_id}/metrics
# ---------------------------------------------------------------------------
class TestGetRunMetrics:
    def test_returns_200_for_valid_run(self):
        response = client.get("/runs/abc123xyz/metrics")
        assert response.status_code == 200

    def test_returns_correct_run_id(self):
        response = client.get("/runs/abc123xyz/metrics")
        assert response.json()["run_id"] == "abc123xyz"

    def test_contains_metrics_and_params(self):
        response = client.get("/runs/abc123xyz/metrics")
        data = response.json()
        assert "metrics" in data
        assert "params" in data
        assert "tags" in data

    def test_accuracy_in_metrics(self):
        response = client.get("/runs/abc123xyz/metrics")
        assert "accuracy" in response.json()["metrics"]

    def test_accuracy_is_float(self):
        response = client.get("/runs/abc123xyz/metrics")
        accuracy = response.json()["metrics"]["accuracy"]
        assert isinstance(accuracy, float)
        assert 0.0 <= accuracy <= 1.0

    def test_returns_404_for_unknown_run(self):
        response = client.get("/runs/does_not_exist/metrics")
        assert response.status_code == 404

    def test_second_run_metrics(self):
        response = client.get("/runs/def456uvw/metrics")
        assert response.status_code == 200
        assert response.json()["metrics"]["accuracy"] == pytest.approx(0.93)


# ---------------------------------------------------------------------------
# DS-006: GET /runs/compare?run_ids=id1,id2
# ---------------------------------------------------------------------------
class TestCompareRuns:
    def test_returns_200_for_valid_run_ids(self):
        response = client.get("/runs/compare?run_ids=abc123xyz,def456uvw")
        assert response.status_code == 200

    def test_response_has_runs_and_winner(self):
        response = client.get("/runs/compare?run_ids=abc123xyz,def456uvw")
        data = response.json()
        assert "runs" in data
        assert "winner" in data

    def test_returns_both_runs(self):
        response = client.get("/runs/compare?run_ids=abc123xyz,def456uvw")
        run_ids = [r["run_id"] for r in response.json()["runs"]]
        assert "abc123xyz" in run_ids
        assert "def456uvw" in run_ids

    def test_winner_is_better_run(self):
        response = client.get("/runs/compare?run_ids=abc123xyz,def456uvw")
        winner = response.json()["winner"]
        # def456uvw has higher accuracy (0.93 vs 0.91)
        assert winner["run_id"] == "def456uvw"

    def test_winner_has_reason(self):
        response = client.get("/runs/compare?run_ids=abc123xyz,def456uvw")
        assert len(response.json()["winner"]["reason"]) > 0

    def test_returns_400_for_single_run_id(self):
        response = client.get("/runs/compare?run_ids=abc123xyz")
        assert response.status_code == 400

    def test_returns_400_for_missing_run_ids(self):
        response = client.get("/runs/compare")
        assert response.status_code == 422  # FastAPI validation error


# ---------------------------------------------------------------------------
# DS-007: GET /runs/{run_id}/compare-deployed
# ---------------------------------------------------------------------------
class TestCompareDeployed:
    def test_returns_200_for_valid_run(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        assert response.status_code == 200

    def test_response_structure(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        data = response.json()
        assert "candidate_run" in data
        assert "deployed_model" in data
        assert "comparison" in data

    def test_candidate_run_id_matches(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        assert response.json()["candidate_run"]["run_id"] == "def456uvw"

    def test_deployed_model_has_name_and_version(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        deployed = response.json()["deployed_model"]
        assert "model_name" in deployed
        assert "version" in deployed

    def test_comparison_has_recommendation(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        recommendation = response.json()["comparison"]["recommendation"]
        assert recommendation in ("PROMOTE", "HOLD", "REJECT")

    def test_best_run_gets_promote(self):
        # def456uvw: accuracy=0.93, deployed: accuracy=0.89 → delta > 0.01 → PROMOTE
        response = client.get("/runs/def456uvw/compare-deployed")
        assert response.json()["comparison"]["recommendation"] == "PROMOTE"

    def test_accuracy_delta_is_positive(self):
        response = client.get("/runs/def456uvw/compare-deployed")
        delta = response.json()["comparison"]["accuracy_delta"]
        assert delta > 0

    def test_returns_404_for_unknown_run(self):
        response = client.get("/runs/nonexistent/compare-deployed")
        assert response.status_code == 404
