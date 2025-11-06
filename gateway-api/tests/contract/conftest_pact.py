"""Pytest configuration and shared fixtures for Pact contract tests."""

import socket
import threading
import time

import pytest
from gateway_api.main import app


@pytest.fixture(scope="module")
def provider_url():
    """Start the Flask app in a separate thread and return its URL.

    This fixture is used by provider contract tests to spin up the actual
    Flask application so it can be verified against consumer contracts.
    """
    # Use port 0 to let the OS assign a free port
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()

    def run_app():
        app.run(port=port, debug=False, use_reloader=False)

    # Start Flask in a daemon thread
    thread = threading.Thread(target=run_app, daemon=True)
    thread.start()

    # Give the server time to start
    time.sleep(1)

    return f"http://localhost:{port}"
