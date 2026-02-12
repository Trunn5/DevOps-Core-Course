"""Unit tests for DevOps Info Service."""
import pytest
from fastapi.testclient import TestClient

from app import app, get_uptime, get_system_info, get_endpoints, SERVICE_INFO


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# --- GET / tests ---

class TestIndexEndpoint:
    """Tests for the main endpoint."""

    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_json(self, client):
        response = client.get("/")
        assert response.headers["content-type"] == "application/json"

    def test_index_has_all_sections(self, client):
        data = client.get("/").json()
        assert "service" in data
        assert "system" in data
        assert "runtime" in data
        assert "request" in data
        assert "endpoints" in data

    def test_index_service_fields(self, client):
        data = client.get("/").json()["service"]
        assert data["name"] == "devops-info-service"
        assert data["version"] == "1.0.0"
        assert data["framework"] == "FastAPI"
        assert "description" in data

    def test_index_system_fields(self, client):
        data = client.get("/").json()["system"]
        for field in ["hostname", "platform", "platform_version",
                      "architecture", "cpu_count", "python_version"]:
            assert field in data
        assert isinstance(data["cpu_count"], int)
        assert data["cpu_count"] > 0

    def test_index_runtime_fields(self, client):
        data = client.get("/").json()["runtime"]
        assert "uptime_seconds" in data
        assert "uptime_human" in data
        assert "current_time" in data
        assert data["timezone"] == "UTC"
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0

    def test_index_request_fields(self, client):
        data = client.get("/").json()["request"]
        assert data["method"] == "GET"
        assert data["path"] == "/"
        assert "client_ip" in data
        assert "user_agent" in data

    def test_index_request_user_agent(self, client):
        response = client.get("/", headers={"User-Agent": "test-agent/1.0"})
        data = response.json()["request"]
        assert data["user_agent"] == "test-agent/1.0"

    def test_index_endpoints_list(self, client):
        data = client.get("/").json()["endpoints"]
        assert isinstance(data, list)
        assert len(data) >= 2
        paths = [e["path"] for e in data]
        assert "/" in paths
        assert "/health" in paths


# --- GET /health tests ---

class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, client):
        data = client.get("/health").json()
        assert "timestamp" in data
        assert len(data["timestamp"]) > 0

    def test_health_has_uptime(self, client):
        data = client.get("/health").json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)
        assert data["uptime_seconds"] >= 0


# --- Error handling tests ---

class TestErrorHandling:
    """Tests for error handlers."""

    def test_404_returns_json(self, client):
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
        assert "path" in data

    def test_404_shows_path(self, client):
        response = client.get("/some/bad/path")
        data = response.json()
        assert data["path"] == "/some/bad/path"


# --- Helper function tests ---

class TestHelperFunctions:
    """Tests for utility functions."""

    def test_get_uptime_returns_dict(self):
        result = get_uptime()
        assert "seconds" in result
        assert "human" in result

    def test_get_uptime_seconds_non_negative(self):
        result = get_uptime()
        assert result["seconds"] >= 0

    def test_get_uptime_human_is_string(self):
        result = get_uptime()
        assert isinstance(result["human"], str)
        assert len(result["human"]) > 0

    def test_get_system_info_fields(self):
        info = get_system_info()
        for field in ["hostname", "platform", "platform_version",
                      "architecture", "cpu_count", "python_version"]:
            assert field in info

    def test_get_endpoints_returns_list(self):
        endpoints = get_endpoints()
        assert isinstance(endpoints, list)
        for ep in endpoints:
            assert "path" in ep
            assert "method" in ep
            assert "description" in ep

    def test_service_info_constant(self):
        assert SERVICE_INFO["name"] == "devops-info-service"
        assert SERVICE_INFO["framework"] == "FastAPI"

