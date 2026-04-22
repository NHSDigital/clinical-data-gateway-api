"""Pytest configuration and shared fixtures for gateway API tests."""

import copy
import os
from collections.abc import Callable
from datetime import timedelta
from typing import Any, cast

import pytest
import requests
from fhir.constants import FHIRSystem

DEFAULT_REQUEST_HEADERS = {
    "Content-Type": "application/fhir+json",
    "Ods-from": "CONSUMER",
    "Ssp-TraceID": "test-trace-id",
}


SIMPLE_PAYLOAD = {
    "resourceType": "Parameters",
    "parameter": [
        {
            "name": "patientNHSNumber",
            "valueIdentifier": {
                "system": FHIRSystem.NHS_NUMBER,
                "value": "9999999999",
            },
        },
    ],
}


class Client:
    """Client for sending HTTP requests"""

    def __init__(
        self,
        base_url: str,
        health_endpoint: str,
        auth_headers: dict[str, str],
        timeout: timedelta = timedelta(seconds=35),
    ):
        self.base_url = base_url
        self.health_endpoint = health_endpoint
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
        url = f"{self.base_url}/{self.health_endpoint}"
        return requests.get(url=url, headers=self._auth_headers, timeout=self._timeout)


@pytest.fixture
def simple_request_payload() -> dict[str, Any]:
    return copy.deepcopy(SIMPLE_PAYLOAD)


@pytest.fixture
def get_headers(env: str, request: pytest.FixtureRequest) -> dict[str, str]:
    """Return auth headers for remote tests, or Apigee token for local."""
    if env == "local":
        token = os.environ.get("APIGEE_ACCESS_TOKEN", "")
        return {"Authorization": f"Bearer {token}"} if token else {}

    nhsd_headers = cast(
        "dict[str, str]", request.getfixturevalue("nhsd_apim_auth_headers")
    )
    apikey_headers = cast(
        "dict[str, str]", request.getfixturevalue("status_endpoint_auth_headers")
    )
    return nhsd_headers | apikey_headers


@pytest.fixture
def client(
    base_url: str,
    health_endpoint: str,
    get_headers: dict[str, str],
) -> Client:
    return Client(
        base_url=base_url, health_endpoint=health_endpoint, auth_headers=get_headers
    )


@pytest.fixture(scope="module")
def env() -> str:
    return get_env()


def get_env() -> str:
    return _fetch_env_variable("TARGET_ENV", str)


@pytest.fixture
def base_url(env: str, request: pytest.FixtureRequest) -> str:
    """Retrieves the base URL of the currently deployed application."""
    if env == "remote":
        return str(request.getfixturevalue("nhsd_apim_proxy_url"))
    return _fetch_env_variable("BASE_URL", str)


@pytest.fixture
def health_endpoint(env: str) -> str:
    if env == "local":
        return "health"
    else:
        return "_status"


def _fetch_env_variable[T](name: str, parser: Callable[[str], T]) -> T:
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"{name} environment variable is not set.")
    return parser(value)


def _get_remote_test_username() -> str:
    """Return the username to use for remote tests, allowing override via env."""
    return _fetch_env_variable("REMOTE_TEST_USERNAME", str)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    target_is_remote = get_env() == "remote"
    if target_is_remote:
        for item in items:
            item.add_marker(
                pytest.mark.nhsd_apim_authorization(
                    access="healthcare_worker",
                    level="aal3",
                    login_form={"username": _get_remote_test_username()},
                )
            )
