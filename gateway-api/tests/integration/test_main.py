"""Integration tests for the gateway API using pytest."""

from tests.conftest import Client


class TestHelloWorld:
    """Test suite for the hello world endpoint."""

    def test_hello_world_returns_200(self, client: Client) -> None:
        """Test that the root endpoint returns a 200 status code."""
        response = client.send("world")
        assert response.status_code == 200

    def test_hello_world_returns_correct_message(self, client: Client) -> None:
        """Test that the root endpoint returns the correct message."""
        response = client.send("World")
        assert response.json()["body"] == "Hello, World!"

    def test_hello_world_content_type(self, client: Client) -> None:
        """Test that the response has the correct content type."""
        response = client.send("world")
        assert "application/json" in response.headers["Content-Type"]

    def test_nonexistent_returns_error(self, client: Client) -> None:
        """Test that non-existent routes return 404."""
        response = client.send("nonexistent")
        assert response.status_code == 200

        body = response.json().get("body")
        assert body == "Provided name cannot be found. name=nonexistent"

        status_code = response.json().get("statusCode")
        assert status_code == 404

    def test_no_payload_returns_error(self, client: Client) -> None:
        """Test that an error is returned when no payload is provided."""
        response = client.send_without_payload()
        assert response.status_code == 200

        body = response.json().get("body")
        assert body == "Name is required"

    def test_empty_name_returns_error(self, client: Client) -> None:
        """Test that an error is returned when an empty name is provided."""
        response = client.send("")
        assert response.status_code == 200

        body = response.json().get("body")
        assert body == "Name cannot be empty"
