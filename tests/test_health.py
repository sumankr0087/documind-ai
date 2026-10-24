"""Automated tests for /health, root, and /ui endpoints."""


def test_health_check_returns_200(test_client):
    """Test that /health returns 200 with complete system details."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["app_env"] == "testing"
    assert "services" in data
    assert "vector_store" in data["services"]
    assert "embedding" in data["services"]
    assert "llm" in data["services"]
    assert data["services"]["vector_store"]["status"] == "connected"


def test_root_endpoint(test_client):
    """Test that root endpoint returns documentation, UI link, and service info."""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "DocuMind AI"
    assert data["documentation"] == "/docs"
    assert "ui" in data


def test_ui_endpoint(test_client):
    """Test that /ui serves the compiled React application."""
    response = test_client.get("/ui")
    assert response.status_code == 200
    assert "DocuMind AI" in response.text
