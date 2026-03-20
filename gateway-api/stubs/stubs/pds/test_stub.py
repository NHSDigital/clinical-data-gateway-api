"""Unit tests for the PDS FHIR R4 API stub (stubs.pds.stub)."""

import uuid
from unittest.mock import patch

import pytest

from stubs.pds.stub import PdsFhirApiStub

# A valid UUID used as X-Request-ID across multiple tests.
_VALID_REQUEST_ID = str(uuid.uuid4())

# NHS numbers that are pre-seeded by PdsFhirApiStub.__init__.
_SEEDED_NHS_NUMBER = "9999999999"  # Alice Jones

# A syntactically valid 10-digit NHS number that is *not* pre-seeded.
_UNKNOWN_NHS_NUMBER = "1234567890"


class TestUpsertPatient:
    """Tests for PdsFhirApiStub.upsert_patient."""

    def setup_method(self) -> None:
        self.stub = PdsFhirApiStub()

    def test_raises_type_error_when_nhs_number_is_not_a_string(self) -> None:
        with pytest.raises(TypeError, match="NHS Number must be a string"):
            self.stub.upsert_patient(nhs_number=1234567890)  # type: ignore[arg-type]

    def test_raises_value_error_for_non_10_digit_nhs_number(self) -> None:
        with pytest.raises(ValueError, match="NHS Number must be exactly 10 digits"):
            self.stub.upsert_patient(nhs_number="123")

    def test_raises_value_error_when_nhs_number_fails_validation(self) -> None:
        with patch.object(PdsFhirApiStub, "_is_valid_nhs_number", return_value=False):
            with pytest.raises(ValueError, match="NHS Number is not valid"):
                self.stub.upsert_patient(nhs_number=_UNKNOWN_NHS_NUMBER)

    def test_none_patient_creates_default_patient_resource(self) -> None:
        self.stub.upsert_patient(nhs_number=_UNKNOWN_NHS_NUMBER, patient=None, version_id=7)

        patient, version_id = self.stub._patients[_UNKNOWN_NHS_NUMBER]
        assert patient["resourceType"] == "Patient"
        assert patient["id"] == _UNKNOWN_NHS_NUMBER
        assert patient["meta"]["versionId"] == "7"
        assert "lastUpdated" in patient["meta"]
        assert version_id == 7


class TestGetPatient:
    """Tests for PdsFhirApiStub.get_patient."""

    def setup_method(self) -> None:
        self.stub = PdsFhirApiStub()

    def test_returns_400_when_request_id_is_missing_in_strict_mode(self) -> None:
        response = self.stub.get_patient(nhs_number=_SEEDED_NHS_NUMBER, request_id=None)

        assert response.status_code == 400
        coding = response.json()["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "INVALID_REQUEST"
        assert "Missing X-Request-ID" in coding["display"]

    def test_returns_400_when_request_id_is_not_a_uuid_in_strict_mode(self) -> None:
        response = self.stub.get_patient(
            nhs_number=_SEEDED_NHS_NUMBER,
            request_id="not-a-uuid",
            correlation_id="corr-abc",
        )

        assert response.status_code == 400
        coding = response.json()["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "INVALID_REQUEST"
        # Both trace headers must be echoed back even on a bad-request response.
        assert response.headers["X-Request-Id"] == "not-a-uuid"
        assert response.headers["X-Correlation-Id"] == "corr-abc"

    def test_allows_missing_request_id_when_strict_headers_disabled(self) -> None:
        stub = PdsFhirApiStub(strict_headers=False)
        response = stub.get_patient(nhs_number=_SEEDED_NHS_NUMBER, request_id=None)

        assert response.status_code == 200

    def test_returns_400_for_non_10_digit_nhs_number(self) -> None:
        response = self.stub.get_patient(
            nhs_number="123",
            request_id=_VALID_REQUEST_ID,
        )

        assert response.status_code == 400
        coding = response.json()["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "INVALID_RESOURCE_ID"

    def test_returns_404_for_unknown_patient(self) -> None:
        response = self.stub.get_patient(
            nhs_number=_UNKNOWN_NHS_NUMBER,
            request_id=_VALID_REQUEST_ID,
        )

        assert response.status_code == 404
        coding = response.json()["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "RESOURCE_NOT_FOUND"

    def test_returns_200_with_patient_etag_and_echoed_trace_headers(self) -> None:
        response = self.stub.get_patient(
            nhs_number=_SEEDED_NHS_NUMBER,
            request_id=_VALID_REQUEST_ID,
            correlation_id="my-correlation-id",
        )

        assert response.status_code == 200
        assert response.headers["ETag"] == 'W/"1"'
        assert response.headers["X-Request-Id"] == _VALID_REQUEST_ID
        assert response.headers["X-Correlation-Id"] == "my-correlation-id"
        body = response.json()
        assert body["resourceType"] == "Patient"
        assert body["id"] == _SEEDED_NHS_NUMBER


class TestGet:
    """Tests for PdsFhirApiStub.get (HTTP-layer adapter)."""

    def test_extracts_nhs_number_and_headers_from_url_and_header_dict(self) -> None:
        stub = PdsFhirApiStub()
        response = stub.get(
            url=f"https://example.com/Patient/{_SEEDED_NHS_NUMBER}",
            headers={
                "X-Request-ID": _VALID_REQUEST_ID,
                "X-Correlation-ID": "cid-123",
                "Authorization": "Bearer token",
            },
        )

        assert response.status_code == 200
        assert response.json()["id"] == _SEEDED_NHS_NUMBER

    def test_works_when_no_headers_dict_is_supplied(self) -> None:
        stub = PdsFhirApiStub(strict_headers=False)
        response = stub.get(
            url=f"https://example.com/Patient/{_SEEDED_NHS_NUMBER}",
            headers=None,
        )

        assert response.status_code == 200


class TestPost:
    """Tests for PdsFhirApiStub.post."""

    def test_raises_not_implemented_error(self) -> None:
        stub = PdsFhirApiStub()
        with pytest.raises(NotImplementedError):
            stub.post(
                url="https://example.com/Patient",
                headers={},
                data={},
                timeout=10,
            )
