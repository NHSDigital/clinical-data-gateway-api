"""Pytest configuration and shared fixtures for gateway API tests."""

import json
from dataclasses import dataclass
from typing import Any

import pytest
import requests
from fhir import Bundle, OperationOutcome, PatientTypedDict
from fhir.parameters import Parameters
from flask import Request
from requests.structures import CaseInsensitiveDict
from werkzeug.test import EnvironBuilder


@dataclass
class FakeResponse:
    """
    Minimal substitute for :class:`requests.Response` used by tests.
    """

    status_code: int
    headers: dict[str, str] | CaseInsensitiveDict[str]
    _json: dict[str, Any] | PatientTypedDict | OperationOutcome | Bundle
    reason: str = ""

    def json(self) -> dict[str, Any] | PatientTypedDict | OperationOutcome | Bundle:
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


def create_mock_request(headers: dict[str, str], body: Parameters) -> Request:
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
def valid_simple_request_payload() -> Parameters:
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
def valid_simple_response_payload() -> Bundle:
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
                                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
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
def happy_path_pds_response_body() -> PatientTypedDict:
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
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                },
            }
        ],
        "gender": "female",
        "birthDate": "1990-05-15",
    }


@pytest.fixture
def auth_token() -> str:
    return "AUTH_TOKEN123"
