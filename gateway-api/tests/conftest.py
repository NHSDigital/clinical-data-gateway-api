"""Pytest configuration and shared fixtures for gateway API tests."""

import json
import os
from datetime import timedelta
from typing import cast

import pytest
import requests
from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file in the workspace root
# find_dotenv searches upward from current directory for .env file
load_dotenv(find_dotenv())


class Client:
    """A simple HTTP client for testing purposes."""

    def __init__(self, lambda_url: str, timeout: timedelta = timedelta(seconds=1)):
        self._lambda_url = lambda_url
        self._timeout = timeout.total_seconds()

    def send(self, data: str) -> requests.Response:
        """
        Send a request to the APIs with some given parameters.
        Args:
            data: The data to send in the request payload
        Returns:
            Response object from the request
        """
        return self._send(data=data, include_payload=True)

    def send_without_payload(self) -> requests.Response:
        """
        Send a request to the APIs without a payload.
        Returns:
            Response object from the request
        """
        return self._send(data=None, include_payload=False)

    def _send(self, data: str | None, include_payload: bool) -> requests.Response:
        json_data = {"payload": data} if include_payload else {}

        return requests.post(
            f"{self._lambda_url}/2015-03-31/functions/function/invocations",
            data=json.dumps(json_data),
            timeout=self._timeout,
        )


@pytest.fixture(scope="module")
def client(base_url: str) -> Client:
    """Create a test client for the application."""
    return Client(lambda_url=base_url)


@pytest.fixture(scope="module")
def base_url() -> str:
    """Retrieves the base URL of the currently deployed application."""
    return _fetch_env_variable("BASE_URL", str)


@pytest.fixture(scope="module")
def hostname() -> str:
    """Retrieves the hostname of the currently deployed application."""
    return _fetch_env_variable("HOSTNAME", str)


def _fetch_env_variable[T](name: str, t: type[T]) -> T:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is not set.")
    return cast("T", value)
