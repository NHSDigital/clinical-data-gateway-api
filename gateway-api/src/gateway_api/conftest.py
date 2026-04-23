"""Pytest configuration and shared fixtures for gateway API tests."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import TracebackType
from typing import Any

import pytest
import requests
from fhir.constants import FHIRSystem
from flask import Request
from requests.structures import CaseInsensitiveDict
from werkzeug.test import EnvironBuilder

from gateway_api.clinical_jwt import JWT


class NewEnvVars:
    def __init__(self, new_env_vars: Mapping[str, str | None]) -> None:
        self.new_env_vars = new_env_vars
        self.original_env_vars = {}
        for key in new_env_vars:
            if key in os.environ:
                self.original_env_vars[key] = os.environ[key]

    def __enter__(self) -> "NewEnvVars":
        for key, value in self.new_env_vars.items():
            if value is None and key in os.environ:
                del os.environ[key]
            elif value is not None:
                os.environ[key] = value
        return self

    def __exit__(
        self,
        _type: type[BaseException] | None,
        _value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        for key in self.new_env_vars:
            if key in os.environ:
                del os.environ[key]
        os.environ.update(self.original_env_vars)


@dataclass
class FakeResponse:
    """
    Minimal substitute for :class:`requests.Response` used by tests.
    """

    status_code: int
    headers: dict[str, str] | CaseInsensitiveDict[str]
    _json: dict[str, Any]
    reason: str = ""

    def json(
        self,
    ) -> dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code != 200:
            err = requests.HTTPError(f"{self.status_code} Error")
            # requests attaches a Response to HTTPError.response; the client expects it
            err.response = self
            raise err

    @property
    def text(self) -> str:
        return json.dumps(self._json)


def create_mock_request(headers: dict[str, str], body: dict[str, Any]) -> Request:
    """Create a proper Flask Request object with headers and JSON body."""
    builder = EnvironBuilder(
        method="POST",
        path="/patient/$gpc.getstructuredrecord",
        data=json.dumps(body),
        content_type="application/fhir+json",
        headers=headers,
    )
    env = builder.get_environ()
    return Request(env)


@pytest.fixture
def valid_simple_request_payload() -> dict[str, Any]:
    return {
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


@pytest.fixture
def valid_simple_response_payload() -> dict[str, Any]:
    return {
        "resourceType": "Bundle",
        "id": "example-patient-bundle",
        "type": "collection",
        "timestamp": "2026-02-05T22:45:42.766330+00:00",
        "entry": [
            {
                "fullUrl": "https://example.com/Patient/9999999999",
                "resource": {
                    "name": [
                        {
                            "family": "Alice",
                            "given": ["Johnson"],
                            "use": "Ally",
                            "period": {"start": "2020-01-01"},
                        }
                    ],
                    "gender": "female",
                    "birthDate": "1990-05-15",
                    "resourceType": "Patient",
                    "id": "9999999999",
                    "identifier": [
                        {
                            "value": "9999999999",
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                        }
                    ],
                    "generalPractitioner": [
                        {
                            "id": "1",
                            "type": "Organization",
                            "identifier": {
                                "value": "A12345",
                                "period": {"start": "2020-01-01", "end": "9999-12-31"},
                                "system": FHIRSystem.ODS_CODE,
                            },
                        }
                    ],
                },
            }
        ],
    }


@pytest.fixture
def valid_headers() -> dict[str, str]:
    return {
        "Ssp-TraceID": "test-trace-id",
        "ODS-from": "test-ods",
        "Content-type": "application/fhir+json",
    }


@pytest.fixture
def happy_path_pds_response_body() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "9999999999",
        "identifier": [
            {"value": "9999999999", "system": "https://fhir.nhs.uk/Id/nhs-number"}
        ],
        "name": [
            {
                "family": "Johnson",
                "given": ["Alice"],
                "use": "Ally",
                "period": {"start": "2020-01-01", "end": "9999-12-31"},
            }
        ],
        "generalPractitioner": [
            {
                "id": "1",
                "type": "Organization",
                "identifier": {
                    "value": "A12345",
                    "period": {"start": "2020-01-01", "end": "9999-12-31"},
                    "system": FHIRSystem.ODS_CODE,
                },
            }
        ],
        "gender": "female",
        "birthDate": "1990-05-15",
    }


@pytest.fixture
def auth_token() -> str:
    return "AUTH_TOKEN123"


@pytest.fixture
def valid_jwt() -> JWT:
    """Create a valid JWT for testing."""
    return JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={
            "resourceType": "Device",
            "identifier": [{"system": "https://example.com/device", "value": "dev123"}],
            "model": "TestModel",
            "version": "1.0",
        },
        requesting_organization={
            "resourceType": "Organization",
            "identifier": [
                {
                    "system": FHIRSystem.ODS_CODE,
                    "value": "T1234",
                }
            ],
            "name": "Test Organization",
        },
        requesting_practitioner={
            "resourceType": "Practitioner",
            "id": "prac123",
            "identifier": [
                {"system": FHIRSystem.SDS_USER_ID, "value": "user123"},
                {
                    "system": FHIRSystem.SDS_ROLE_PROFILE_ID,
                    "value": "role123",
                },
                {"system": "https://example.com/userid", "value": "userid123"},
            ],
            "name": [{"family": "TestPractitioner", "given": ["Test"]}],
        },
    )
