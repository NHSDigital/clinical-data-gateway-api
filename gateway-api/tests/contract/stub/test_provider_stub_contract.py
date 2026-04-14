"""
Contract tests for the ProviderStub class.

These tests verify that the :class:`~stubs.provider.stub.GpProviderStub` honours the
``POST /Patient/$gpc.getstructuredrecord`` contract described in the specification:
https://webarchive.nationalarchives.gov.uk/ukgwa/20250305141535/https://developer.nhs.uk/apis/gpconnect-1-5-0/accessrecord_structured_development_retrieve_patient_record.html

The stub does not expose an HTTP server, so the tests call its methods directly
and validate the returned :class:`requests.Response` objects against the
contract requirements.
"""

import json
from typing import Any

import pytest
from gateway_api.common.error import JWTValidationError
from pytest_mock import MockerFixture
from stubs.data.patients.patients import Patients
from stubs.provider.stub import GpProviderStub

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------
_URL = "http://example.com/Patient/$gpc.getstructuredrecord"
_VALID_HEADERS = {
    "Ssp-TraceID": "test-trace-id-12345",
    "Ssp-From": "999999999999",
    "Ssp-To": "999999999999",
    "Ssp-InteractionID": (
        "urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1"
    ),
    "Content-Type": "application/fhir+json",
    "Authorization": "Bearer some-valid-jwt-token",
}
_ACCESS_RECORD_STRUCTURED_INTERACTION_ID = (
    "urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1"
)


# patch JWTValidator.validate to always pass for testing


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider_stub() -> GpProviderStub:
    """Fixture that returns a new instance of the provider stub."""
    return GpProviderStub()


# ---------------------------------------------------------------------------
# POST /Patient/$gpc.getstructuredrecord – 200 success
# ---------------------------------------------------------------------------


class TestGetStructuredRecordSuccess:
    """
    Tests for successful responses from the ``POST /Patient/$gpc.getstructuredrecord``
    endpoint.
    """

    def test_get_structured_record_success(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        response = provider_stub.post(
            url=_URL,
            headers=_VALID_HEADERS,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "collection"
        assert body["meta"] == {
            "profile": [
                "https://fhir.nhs.uk/STU3/StructureDefinition/GPConnect-StructuredRecord-Bundle-1"
            ]
        }

        entry = body["entry"]
        assert len(entry) == 1

        resource = entry[0]["resource"]
        assert resource == Patients.ALICE_JONES_9999999999


# ---------------------------------------------------------------------------
# POST /Patient/$gpc.getstructuredrecord – 400 validation errors
# JWT VALIDATIONS? mocked
# missing params
# ---------------------------------------------------------------------------
class TestGetStructuredRecordValidationErrors:
    """
    Tests for validation errors from the ``POST /Patient/$gpc.getstructuredrecord``
    endpoint.
    """

    def test_get_structured_record_missing_headers(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        response = provider_stub.post(
            url=_URL,
            headers={},  # Missing all required headers
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert body["issue"][0]["diagnostics"].count("is required") == 6
        diagnostics = body["issue"][0]["diagnostics"]
        for header in [
            "Ssp-TraceID",
            "Ssp-From",
            "Ssp-To",
            "Ssp-InteractionID",
            "Content-Type",
            "Authorization",
        ]:
            assert header in diagnostics

    def test_get_structured_record_invalid_content_type(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        invalid_headers = _VALID_HEADERS.copy()
        invalid_headers["Content-Type"] = "text/plain"
        response = provider_stub.post(
            url=_URL,
            headers=invalid_headers,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert (
            "Content-Type must be application/fhir+json"
            in body["issue"][0]["diagnostics"]
        )

    def test_get_structured_record_invalid_interaction_id(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        invalid_headers = _VALID_HEADERS.copy()
        invalid_headers["Ssp-InteractionID"] = "invalid-interaction-id"
        response = provider_stub.post(
            url=_URL,
            headers=invalid_headers,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert (
            f"Ssp-InteractionID: expected "
            f"{_ACCESS_RECORD_STRUCTURED_INTERACTION_ID}"
            in body["issue"][0]["diagnostics"]
        )

    def test_get_structured_record_jwt_does_not_start_with_bearer(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        invalid_headers = _VALID_HEADERS.copy()
        invalid_headers["Authorization"] = "not-bearer token"
        response = provider_stub.post(
            url=_URL,
            headers=invalid_headers,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert isinstance(body["issue"][0]["diagnostics"], str)
        assert (
            "Authorization header must start with 'Bearer '"
            in body["issue"][0]["diagnostics"]
        )

    def test_jwt_cannot_be_decoded(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch(
            "stubs.provider.stub.JWT.decode", side_effect=Exception("Decode error")
        )
        response = provider_stub.post(
            url=_URL,
            headers=_VALID_HEADERS,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert "Invalid JWT: Decode error" in body["issue"][0]["diagnostics"]

    def test_jwt_fails_validation(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
        simple_request_payload: dict[str, Any],
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch(
            "stubs.provider.stub.JWTValidator.validate",
            side_effect=JWTValidationError(error_details="Validation error"),
        )
        response = provider_stub.post(
            url=_URL,
            headers=_VALID_HEADERS,
            data=json.dumps(simple_request_payload),
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert "Validation error" in body["issue"][0]["diagnostics"]

    def test_get_structured_record_missing_body(
        self,
        provider_stub: GpProviderStub,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch("stubs.provider.stub.JWT.decode", return_value="some-decoded-jwt")
        mocker.patch("stubs.provider.stub.JWTValidator.validate", return_value=None)
        response = provider_stub.post(
            url=_URL,
            headers=_VALID_HEADERS,
            data=None,
        )

        assert response.status_code == 400
        assert response.headers["Content-Type"] == "application/fhir+json"

        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert len(body["issue"]) == 1
        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"
        assert "body is required" in body["issue"][0]["diagnostics"]
