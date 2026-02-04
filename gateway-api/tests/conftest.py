"""Pytest configuration and shared fixtures for gateway API tests."""

import os
from datetime import timedelta

import pytest
import requests
from dotenv import find_dotenv, load_dotenv
from fhir.bundle import Bundle
from fhir.parameters import Parameters

# Load environment variables from .env file in the workspace root
# find_dotenv searches upward from current directory for .env file
load_dotenv(find_dotenv())


class Client:
    """A simple HTTP client for testing purposes."""

    def __init__(
        self,
        base_url: str,
        cert: tuple[str, str] | None = None,
        timeout: timedelta = timedelta(seconds=5),
    ):
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout.total_seconds()
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
        return requests.get(url=url, timeout=self._timeout)


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


# TODO: Pretty sure we don't need this any more
@pytest.fixture
def expected_response_payload() -> Bundle:
    return {
        "resourceType": "Bundle",
        "id": "example-patient-bundle",
        "type": "collection",
        "timestamp": "2026-01-12T10:00:00Z",
        "entry": [
            {
                "fullUrl": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
                "resource": {
                    "resourceType": "Patient",
                    "id": "9999999999",
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9999999999",
                        }
                    ],
                    "name": [{"use": "official", "family": "Doe", "given": ["John"]}],
                    "gender": "male",
                    "birthDate": "1985-04-12",
                },
            }
        ],
    }


@pytest.fixture(scope="module")
def client(base_url: str) -> Client:
    """Create a test client for the application."""
    return Client(base_url=base_url)


@pytest.fixture(scope="module")
def base_url() -> str:
    """Retrieves the base URL of the currently deployed application."""
    return _fetch_env_variable("BASE_URL")


@pytest.fixture(scope="module")
def hostname() -> str:
    """Retrieves the hostname of the currently deployed application."""
    return _fetch_env_variable("HOST")


def _fetch_env_variable(name: str) -> str:
    """Return the environment variable `name` as a string or raise a ValueError."""
    value = os.getenv(name)
    if value is None or value == "":
        raise ValueError(f"{name} environment variable is not set.")
    return value
