"""Unit tests for the gateway API using pytest."""


class TestHelloWorld:
    """Test suite for the hello world endpoint."""

    def test_hello_world_returns_200(self, client):
        """Test that the root endpoint returns a 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_hello_world_returns_correct_message(self, client):
        """Test that the root endpoint returns the correct message."""
        response = client.get("/")
        assert response.text == "Hello, World!"

    def test_hello_world_content_type(self, client):
        """Test that the response has the correct content type."""
        response = client.get("/")
        assert "text/html" in response.content_type

    def test_nonexistent_route_returns_404(self, client):
        """Test that non-existent routes return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
