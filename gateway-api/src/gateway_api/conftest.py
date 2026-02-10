"""Pytest configuration and shared fixtures for gateway API tests."""

import pytest
from fhir.bundle import Bundle
from fhir.parameters import Parameters


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
                    "name": [{"family": "Alice", "given": ["Johnson"], "use": "Ally"}],
                    "gender": "female",
                    "birthDate": "1990-05-15",
                    "resourceType": "Patient",
                    "id": "9999999999",
                    "identifier": [
                        {"value": "9999999999", "system": "urn:nhs:numbers"}
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
def auth_token() -> str:
    return "AUTH_TOKEN123"
