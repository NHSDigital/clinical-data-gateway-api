"""Pytest configuration and shared fixtures for gateway API tests."""

import pytest
from gateway_api.main import app as flask_app


@pytest.fixture
def app():
    """Create and configure a test instance of the Flask application."""
    flask_app.config.update(
        {
            "TESTING": True,
        }
    )

    return flask_app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()
