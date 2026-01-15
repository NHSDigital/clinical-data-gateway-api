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

    def get_structured_record(self, nhs_number: str) -> requests.Response:
        """
        Send a request to the get_structured_record endpoint with the given NHS number.
        """
        payload = json.dumps(
            {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "patientNHSNumber",
                        "valueIdentifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": nhs_number,
                        },
                    },
                ],
            }
        )
        url = f"{self._lambda_url}/patient/$gpc.getstructuredrecord"
        return self._send(url=url, payload=payload)

    def send(self, message: str) -> requests.Response:
        """
        Send a request to the APIs with some given parameters.
        Args:
            data: The data to send in the request payload
        Returns:
            Response object from the request
        """
        payload = json.dumps({"payload": message})
        url = f"{self._lambda_url}/2015-03-31/functions/function/invocations"
        return self._send(url=url, payload=payload)

    def send_without_payload(self) -> requests.Response:
        """
        Send a request to the APIs without a payload.
        Returns:
            Response object from the request
        """
        empty_payload = json.dumps({})
        url = f"{self._lambda_url}/2015-03-31/functions/function/invocations"
        return self._send(url=url, payload=empty_payload)

    def _send(self, url: str, payload: str) -> requests.Response:
        return requests.post(
            url=url,
            data=payload,
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
    return _fetch_env_variable("HOST", str)


def _fetch_env_variable[T](name: str, t: type[T]) -> T:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is not set.")
    return cast("T", value)
