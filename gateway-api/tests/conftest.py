"""Pytest configuration and shared fixtures for gateway API tests."""

import socket
import threading
import time

import pytest
import requests
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
    # Daemon threads automatically terminate when the test process exits,
    # so no explicit cleanup is needed
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # Wait for server to be ready by polling the hello world endpoint
    url = f"http://localhost:{port}"
    max_retries = 10
    retry_delay = 0.1  # 100ms between retries

    for _ in range(max_retries):
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            # Server not ready yet, wait and retry
            time.sleep(retry_delay)
    else:
        raise RuntimeError(f"Flask server failed to start on {url}")

    return url
