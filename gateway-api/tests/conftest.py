"""Pytest configuration and shared fixtures for gateway API tests."""

import os
from datetime import timedelta
from typing import cast

import pytest
import requests
from dotenv import find_dotenv, load_dotenv
from fhir.parameters import Parameters

# Load environment variables from .env file in the workspace root
# find_dotenv searches upward from current directory for .env file
load_dotenv(find_dotenv())


class Client:
    """A simple HTTP client for testing purposes."""

    def __init__(self, base_url: str, timeout: timedelta = timedelta(seconds=1)):
        self.base_url = base_url
        self._timeout = timeout.total_seconds()

        cert = None
        cert_path = os.getenv("MTLS_CERT")
        key_path = os.getenv("MTLS_KEY")
        if cert_path and key_path:
            cert = (cert_path, key_path)
        self._cert = cert

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        """
        Send a request to the get_structured_record endpoint with the given NHS number.
        """
        url = f"{self.base_url}/patient/$gpc.getstructuredrecord"
        default_headers = {
            "Content-Type": "application/fhir+json",
            "Ods-from": "test-ods-code",
            "Ssp-TraceID": "test-trace-id",
        }
        if headers:
            default_headers.update(headers)
        return requests.post(
            url=url,
            data=payload,
            headers=default_headers,
            timeout=self._timeout,
            cert=self._cert,
        )

    def send_health_check(self) -> requests.Response:
        """
        Send a health check request to the API.
        Returns:
            Response object from the request
        """
        url = f"{self.base_url}/health"
        return requests.get(url=url, timeout=self._timeout, cert=self._cert)


@pytest.fixture
def simple_request_payload() -> Parameters:
    return {
        "resourceType": "Parameters",
        "parameter": [
            {
                "name": "patientNHSNumber",
                "valueIdentifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "9999999999",
                },
            },
        ],
    }


@pytest.fixture(scope="module")
def client(base_url: str) -> Client:
    """Create a test client for the application."""
    return Client(base_url=base_url)


@pytest.fixture(scope="module")
def base_url() -> str:
    """Retrieves the base URL of the currently deployed application."""
    return _fetch_env_variable("BASE_URL", str)


@pytest.fixture(scope="module")
def hostname() -> str:
    """Retrieves the hostname of the currently deployed application."""
    return _fetch_env_variable("HOST", str)


def _fetch_env_variable[T](
    name: str,
    t: type[T],  # NOQA ARG001 This is actually used for type hinting
) -> T:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} environment variable is not set.")
    return cast("T", value)
