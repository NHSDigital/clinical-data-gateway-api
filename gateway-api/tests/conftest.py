"""Pytest configuration and shared fixtures for gateway API tests."""

import os
from datetime import timedelta
from typing import Any, Protocol, cast

import pytest
import requests
from dotenv import find_dotenv, load_dotenv
from fhir.parameters import Parameters

# Load environment variables from .env file in the workspace root
load_dotenv(find_dotenv())


class Client(Protocol):
    """Protocol defining the interface for HTTP clients."""

    base_url: str
    cert: tuple[str, str] | None

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        """
        Send a request to the get_structured_record endpoint with the given NHS number.
        """
        ...

    def send_health_check(self) -> requests.Response:
        """
        Send a health check request to the API.
        """
        ...


class LocalClient:
    """HTTP client that sends requests directly to the API (no proxy auth)."""

    def __init__(
        self,
        base_url: str,
        cert: tuple[str, str] | None = None,
        timeout: timedelta = timedelta(seconds=1),
    ):
        self.base_url = base_url
        self.cert = cert
        self._timeout = timeout.total_seconds()

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        url = f"{self.base_url}/patient/$gpc.getstructuredrecord"
        default_headers = {
            "Content-Type": "application/fhir+json",
            "Ods-from": "CONSUMER",
            "Ssp-TraceID": "test-trace-id",
        }
        if headers:
            default_headers.update(headers)

        return requests.post(
            url=url,
            data=payload,
            headers=default_headers,
            timeout=self._timeout,
            cert=self.cert,
        )

    def send_health_check(self) -> requests.Response:
        url = f"{self.base_url}/health"
        return requests.get(url=url, timeout=self._timeout, cert=self.cert)


class RemoteClient:
    """HTTP client for remote testing via the APIM proxy."""

    def __init__(
        self,
        api_url: str,
        auth_headers: dict[str, str],
        cert: tuple[str, str] | None = None,
        timeout: timedelta = timedelta(seconds=5),
    ):
        self.base_url = api_url
        self.cert = cert
        self._auth_headers = auth_headers
        self._timeout = timeout.total_seconds()

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        url = f"{self.base_url}/patient/$gpc.getstructuredrecord"

        default_headers = self._auth_headers | {
            "Content-Type": "application/fhir+json",
            "Ods-from": "A12345",
            "Ssp-TraceID": "test-trace-id",
        }
        if headers:
            default_headers.update(headers)

        return requests.post(
            url=url,
            data=payload,
            headers=default_headers,
            timeout=self._timeout,
            cert=self.cert,
        )

    def send_health_check(self) -> requests.Response:
        url = f"{self.base_url}/health"
        return requests.get(
            url=url, headers=self._auth_headers, timeout=self._timeout, cert=self.cert
        )


@pytest.fixture(scope="session")
def mtls_cert() -> tuple[str, str] | None:
    """Returns the mTLS certificate and key paths if provided in the environment."""
    cert_path = os.getenv("MTLS_CERT")
    key_path = os.getenv("MTLS_KEY")

    if cert_path and key_path:
        return (cert_path, key_path)

    return None


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


@pytest.fixture
def get_headers(request: pytest.FixtureRequest) -> Any:
    """Return merged auth headers for remote tests, or empty dict for local."""
    env = request.config.getoption("--env")
    if env == "remote":
        apikey_headers = request.getfixturevalue("status_endpoint_auth_headers")
        nhsd_headers = request.getfixturevalue("nhsd_apim_auth_headers")
        headers = nhsd_headers | apikey_headers
        return headers

    return {}


@pytest.fixture
def client(
    request: pytest.FixtureRequest,
    base_url: str,
    mtls_cert: tuple[str, str] | None,
) -> Client:
    """Create the appropriate HTTP client."""
    env = os.getenv("ENV") or request.config.getoption("--env")

    if env == "local":
        return LocalClient(base_url=base_url, cert=mtls_cert)
    elif env == "remote":
        proxy_url = request.getfixturevalue("nhsd_apim_proxy_url")

        apikey_headers = request.getfixturevalue("status_endpoint_auth_headers")
        token = os.getenv("APIGEE_ACCESS_TOKEN")

        if token:
            auth_headers = {"Authorization": f"Bearer {token}", **apikey_headers}
        else:
            nhsd_headers = request.getfixturevalue("nhsd_apim_auth_headers")
            auth_headers = nhsd_headers | apikey_headers

        return RemoteClient(
            api_url=proxy_url, auth_headers=auth_headers, cert=mtls_cert
        )
    else:
        raise ValueError(f"Unknown env: {env}")


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


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--env",
        action="store",
        default="local",
        help="Environment to run tests against",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    env = os.getenv("ENV") or config.getoption("--env")

    if env == "local":
        skip_remote = pytest.mark.skip(reason="Test only runs in remote environment")
        for item in items:
            if item.get_closest_marker("remote_only"):
                item.add_marker(skip_remote)

    if env == "remote":
        for item in items:
            item.add_marker(
                pytest.mark.nhsd_apim_authorization(
                    access="application", level="level3"
                )
            )
