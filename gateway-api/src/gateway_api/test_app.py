"""Unit tests for the Flask app endpoints."""

import pytest
from flask.testing import FlaskClient

from gateway_api.app import app


@pytest.fixture
def client() -> FlaskClient:
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGreetEndpoint:
    """Unit tests for the greet_endpoint function."""

    def test_greet_endpoint_returns_greeting_for_valid_name(
        self, client: FlaskClient
    ) -> None:
        """Test that greet_endpoint returns a greeting for a valid name."""
        response = client.post(
            "/2015-03-31/functions/function/invocations",
            json={"payload": "Alice"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 200
        assert data["headers"]["Content-Type"] == "application/json"
        assert "Alice" in data["body"]
        assert data["body"].endswith("!")

    def test_greet_endpoint_returns_400_when_payload_missing(
        self, client: FlaskClient
    ) -> None:
        """Test that greet_endpoint returns 400 when payload is missing."""
        response = client.post(
            "/2015-03-31/functions/function/invocations",
            json={},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 400
        assert data["body"] == "Name is required"
        assert data["headers"]["Content-Type"] == "application/json"

    def test_greet_endpoint_returns_400_when_name_is_empty(
        self, client: FlaskClient
    ) -> None:
        """Test that greet_endpoint returns 400 when name is empty."""
        response = client.post(
            "/2015-03-31/functions/function/invocations",
            json={"payload": ""},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 400
        assert data["body"] == "Name cannot be empty"
        assert data["headers"]["Content-Type"] == "application/json"

    def test_greet_endpoint_returns_404_for_nonexistent_user(
        self, client: FlaskClient
    ) -> None:
        """Test that greet_endpoint returns 404 for nonexistent user."""
        response = client.post(
            "/2015-03-31/functions/function/invocations",
            json={"payload": "nonexistent"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 404
        assert "cannot be found" in data["body"]
        assert "nonexistent" in data["body"]
        assert data["headers"]["Content-Type"] == "application/json"

    def test_greet_endpoint_returns_400_when_name_is_none(
        self, client: FlaskClient
    ) -> None:
        """Test that greet_endpoint returns 400 when name is None."""
        response = client.post(
            "/2015-03-31/functions/function/invocations",
            json={"payload": None},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 400
        assert data["body"] == "Name cannot be empty"
        assert data["headers"]["Content-Type"] == "application/json"


class TestHealthCheck:
    """Unit tests for the health_check function."""

    def test_health_check_returns_200_and_healthy_status(
        self, client: FlaskClient
    ) -> None:
        """Test that health_check returns 200 with healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["statusCode"] == 200
        assert data["body"]["status"] == "healthy"
        assert data["headers"]["Content-Type"] == "application/json"

    def test_health_check_only_accepts_get_method(self, client: FlaskClient) -> None:
        """Test that health_check only accepts GET method."""
        response = client.post("/health")
        assert response.status_code == 405  # Method Not Allowed

        response = client.put("/health")
        assert response.status_code == 405

        response = client.delete("/health")
        assert response.status_code == 405
