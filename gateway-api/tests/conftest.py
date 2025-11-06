"""Pytest configuration and shared fixtures for gateway API tests."""

import socket
import threading
import time

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


@pytest.fixture(scope="module")
def provider_url():
    """Start the Flask app in a separate thread and return its URL.

    This fixture is used by tests that need to make real HTTP requests
    to the Flask application (e.g., contract tests, schema tests).
    """
    # Use port 0 to let the OS assign a free port
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    def run_app():
        flask_app.run(port=port, debug=False, use_reloader=False)

    # Start Flask in a daemon thread
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # Give the server time to start
    time.sleep(1)

    return f"http://localhost:{port}"
