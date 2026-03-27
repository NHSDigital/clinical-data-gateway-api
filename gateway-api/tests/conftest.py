"""Pytest configuration and shared fixtures for gateway API tests."""

import os
from datetime import timedelta
from typing import Protocol, cast

import pytest
import requests
from dotenv import find_dotenv, load_dotenv
from fhir.parameters import Parameters

# Load environment variables from .env file in the workspace root
load_dotenv(find_dotenv(usecwd=True))


DEFAULT_REQUEST_HEADERS = {
    "Content-Type": "application/fhir+json",
    "Ods-from": "CONSUMER",
    "Ssp-TraceID": "test-trace-id",
}


class Client(Protocol):
    """Protocol defining the interface for HTTP clients."""

    base_url: str

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

    def send_post_to_path(
        self,
        path: str,
        payload: str,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        """Send a POST request to the given API path."""
        ...


class LocalClient:
    """HTTP client that sends requests directly to the API (no proxy auth)."""

    def __init__(
        self,
        base_url: str,
        timeout: timedelta = timedelta(seconds=35),
    ):
        self.base_url = base_url
        self._timeout = timeout.total_seconds()

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        return self.send_post_to_path(
            path="/patient/$gpc.getstructuredrecord",
            payload=payload,
            headers=headers,
        )

    def send_post_to_path(
        self,
        path: str,
        payload: str,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        default_headers = DEFAULT_REQUEST_HEADERS.copy()
        if headers:
            default_headers.update(headers)

        return requests.post(
            url=url,
            data=payload,
            headers=default_headers,
            timeout=self._timeout,
        )

    def send_health_check(self) -> requests.Response:
        url = f"{self.base_url}/health"
        return requests.get(url=url, timeout=self._timeout)


class RemoteClient:
    """HTTP client for remote testing via the APIM proxy."""

    def __init__(
        self,
        base_url: str,
        auth_headers: dict[str, str],
        timeout: timedelta = timedelta(seconds=35),
    ):
        self.base_url = base_url
        self._auth_headers = auth_headers
        self._timeout = timeout.total_seconds()

    def send_to_get_structured_record_endpoint(
        self, payload: str, headers: dict[str, str] | None = None
    ) -> requests.Response:
        return self.send_post_to_path(
            path="/patient/$gpc.getstructuredrecord",
            payload=payload,
            headers=headers,
        )

    def send_post_to_path(
        self,
        path: str,
        payload: str,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"

        default_headers = self._auth_headers | DEFAULT_REQUEST_HEADERS
        if headers:
            default_headers.update(headers)

        return requests.post(
            url=url,
            data=payload,
            headers=default_headers,
            timeout=self._timeout,
        )

    def send_health_check(self) -> requests.Response:
        url = f"{self.base_url}/_status"
        return requests.get(url=url, headers=self._auth_headers, timeout=self._timeout)


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
def get_headers(request: pytest.FixtureRequest) -> dict[str, str]:
    """Return merged auth headers for remote tests, or empty dict for local."""
    env = request.config.getoption("--env")
    if env == "remote":
        nhsd_headers = cast(
            "dict[str, str]", request.getfixturevalue("nhsd_apim_auth_headers")
        )
        apikey_headers = cast(
            "dict[str, str]", request.getfixturevalue("status_endpoint_auth_headers")
        )
        return nhsd_headers | apikey_headers

    return {}


@pytest.fixture
def client(
    request: pytest.FixtureRequest,
    base_url: str,
) -> Client:
    """Create the appropriate HTTP client."""
    env = request.config.getoption("--env")

    if env == "local":
        return LocalClient(base_url=base_url)
    elif env == "remote":
        proxy_url = request.getfixturevalue("nhsd_apim_proxy_url")
        auth_headers = request.getfixturevalue("nhsd_apim_auth_headers")
        apikey_headers = request.getfixturevalue("status_endpoint_auth_headers")
        auth_headers = auth_headers | apikey_headers

        return RemoteClient(base_url=proxy_url, auth_headers=auth_headers)
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


REMOTE_TEST_USERNAME_ENV_VAR = "REMOTE_TEST_USERNAME"
DEFAULT_REMOTE_TEST_USERNAME = "656005750104"


def _get_remote_test_username() -> str:
    """Return the username to use for remote tests, allowing override via env."""
    return os.getenv(REMOTE_TEST_USERNAME_ENV_VAR, DEFAULT_REMOTE_TEST_USERNAME)


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
    env = config.getoption("--env")

    if env == "local":
        skip_remote = pytest.mark.skip(reason="Test only runs in remote environment")
        for item in items:
            if item.get_closest_marker("remote_only"):
                item.add_marker(skip_remote)

    if env == "remote":
        for item in items:
            item.add_marker(
                pytest.mark.nhsd_apim_authorization(
                    access="healthcare_worker",
                    level="aal3",
                    login_form={"username": _get_remote_test_username()},
                )
            )
