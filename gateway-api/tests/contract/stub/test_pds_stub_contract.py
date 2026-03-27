"""Contract tests for the PDS FHIR API stub.

These tests verify that the :class:`~stubs.pds.stub.PdsFhirApiStub` honours the
``GET /Patient/{id}`` contract described in the PDS OpenAPI specification:

    https://github.com/NHSDigital/personal-demographics-service-api/blob/master/specification/personal-demographics.yaml

The stub does not expose an HTTP server, so the tests call its methods directly
and validate the returned :class:`requests.Response` objects against the
contract requirements.
"""

import re
import uuid

import pytest
import requests
from stubs.pds.stub import PdsFhirApiStub

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

_ETAG_PATTERN = re.compile(r'^W/"[0-9]+"$')

# NHS numbers pre-seeded in the stub
_KNOWN_NHS_NUMBER = "9000000009"  # Jane Smith

# A syntactically valid 10-digit number that is *not* pre-seeded
_UNKNOWN_NHS_NUMBER = "9000000001"

# A string that is clearly not a 10-digit NHS number
_INVALID_NHS_NUMBER = "ABC123"

_VALID_REQUEST_ID = str(uuid.uuid4()).upper()
_VALID_CORRELATION_ID = str(uuid.uuid4()).upper()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub() -> PdsFhirApiStub:
    """Return a stub with strict header validation enabled (the default)."""
    instance = PdsFhirApiStub(strict_headers=True)
    assert (
        instance.get_patient(
            nhs_number=_UNKNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        ).status_code
        == 404
    ), (
        f"NHS number {_UNKNOWN_NHS_NUMBER!r} must not be pre-seeded in the stub; "
        "update _UNKNOWN_NHS_NUMBER to a number that is not in the store."
    )
    return instance


@pytest.fixture
def relaxed_stub() -> PdsFhirApiStub:
    """Return a stub with strict header validation disabled."""
    return PdsFhirApiStub(strict_headers=False)


# ---------------------------------------------------------------------------
# 200 – successful retrieval
# ---------------------------------------------------------------------------


class TestGetPatientSuccess:
    """Contract tests for the happy-path GET /Patient/{id} → 200 response."""

    def test_status_code_is_200(self, stub: PdsFhirApiStub) -> None:
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert response.status_code == 200

    def test_content_type_is_fhir_json(self, stub: PdsFhirApiStub) -> None:
        """The spec mandates ``application/fhir+json`` on every response."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert "application/fhir+json" in response.headers["Content-Type"]

    def test_response_body_resource_type_is_patient(self, stub: PdsFhirApiStub) -> None:
        """The response body must be a FHIR Patient resource."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        assert body["resourceType"] == "Patient"

    def test_response_body_id_matches_requested_nhs_number(
        self, stub: PdsFhirApiStub
    ) -> None:
        """``Patient.id`` must equal the NHS number used in the request path."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        assert body["id"] == _KNOWN_NHS_NUMBER

    def test_response_body_has_meta_version_id(self, stub: PdsFhirApiStub) -> None:
        """``Patient.meta.versionId`` must be present as a string."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        assert "meta" in body
        assert isinstance(body["meta"]["versionId"], str)

    def test_etag_header_present(self, stub: PdsFhirApiStub) -> None:
        """The spec requires an ``ETag`` response header on successful retrieval."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert "ETag" in response.headers

    def test_etag_header_format(self, stub: PdsFhirApiStub) -> None:
        """ETag must follow the ``W/"<integer>"`` format defined in the spec."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        etag = response.headers["ETag"]
        assert _ETAG_PATTERN.match(etag), f'ETag {etag!r} does not match W/"<n>"'

    def test_etag_corresponds_to_meta_version_id(self, stub: PdsFhirApiStub) -> None:
        """The ETag value must correspond to ``Patient.meta.versionId``."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        version_id = body["meta"]["versionId"]
        expected_etag = f'W/"{version_id}"'
        assert response.headers["ETag"] == expected_etag

    def test_x_request_id_echoed_back(self, stub: PdsFhirApiStub) -> None:
        """
        The spec states that ``X-Request-ID`` is mirrored back as ``X-Request-Id``.
        """
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert response.headers.get("X-Request-Id") == _VALID_REQUEST_ID

    def test_x_correlation_id_echoed_back_when_provided(
        self, stub: PdsFhirApiStub
    ) -> None:
        """
        The spec states that ``X-Correlation-ID`` is mirrored back
        as ``X-Correlation-Id``.
        """
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER,
            request_id=_VALID_REQUEST_ID,
            correlation_id=_VALID_CORRELATION_ID,
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

    def test_x_correlation_id_absent_when_not_provided(
        self, stub: PdsFhirApiStub
    ) -> None:
        """``X-Correlation-Id`` must not appear in the response when not supplied."""
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert "X-Correlation-Id" not in response.headers


# ---------------------------------------------------------------------------
# 404 – patient not found
# ---------------------------------------------------------------------------


class TestGetPatientNotFound:
    """Contract tests for GET /Patient/{id} → 404 when the patient does not exist."""

    def test_status_code_is_404(self, stub: PdsFhirApiStub) -> None:
        response = stub.get_patient(
            nhs_number=_UNKNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        assert response.status_code == 404

    def test_operation_outcome_spine_code_is_resource_not_found(
        self, stub: PdsFhirApiStub
    ) -> None:
        """The spec maps 404 patient-not-found to the ``RESOURCE_NOT_FOUND`` code."""
        response = stub.get_patient(
            nhs_number=_UNKNOWN_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        coding = body["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "RESOURCE_NOT_FOUND"


# ---------------------------------------------------------------------------
# 400 – invalid NHS number in path parameter
# ---------------------------------------------------------------------------


class TestGetPatientInvalidNhsNumber:
    """Contract tests for GET /Patient/{id} → 400 when the NHS number is invalid.

    The PDS spec states:
        400 INVALID_RESOURCE_ID – Invalid NHS number.
    """

    @pytest.mark.parametrize(
        "bad_nhs_number",
        [
            "ABC123",  # not digits
            "123",  # too short
            "12345678901",  # too long (11 digits)
            "",  # empty string
        ],
    )
    def test_status_code_is_400(
        self, stub: PdsFhirApiStub, bad_nhs_number: str
    ) -> None:
        response = stub.get_patient(
            nhs_number=bad_nhs_number, request_id=_VALID_REQUEST_ID
        )
        assert response.status_code == 400

    def test_spine_code_is_invalid_resource_id(self, stub: PdsFhirApiStub) -> None:
        """The spec maps an invalid NHS number to ``INVALID_RESOURCE_ID``."""
        response = stub.get_patient(
            nhs_number=_INVALID_NHS_NUMBER, request_id=_VALID_REQUEST_ID
        )
        body = response.json()
        coding = body["issue"][0]["details"]["coding"][0]
        assert coding["code"] == "INVALID_RESOURCE_ID"


# ---------------------------------------------------------------------------
# 400 – missing X-Request-ID (strict mode)
# ---------------------------------------------------------------------------


class TestGetPatientMissingRequestId:
    """Contract tests for GET /Patient/{id} → 400 when ``X-Request-ID`` is absent.

    The PDS spec marks ``X-Request-ID`` as a mandatory header.
    """

    def test_status_code_is_400_when_request_id_absent(
        self, stub: PdsFhirApiStub
    ) -> None:
        response = stub.get_patient(nhs_number=_KNOWN_NHS_NUMBER, request_id=None)
        assert response.status_code == 400

    def test_no_request_id_validation_in_relaxed_mode(
        self, relaxed_stub: PdsFhirApiStub
    ) -> None:
        """In non-strict mode the stub allows absent ``X-Request-ID``."""
        response = relaxed_stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id=None
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 400 – invalid X-Request-ID format (strict mode)
# ---------------------------------------------------------------------------


class TestGetPatientInvalidRequestId:
    """Contract tests for GET /Patient/{id} → 400 when ``X-Request-ID`` is not a UUID.

    The PDS spec requires ``X-Request-ID`` to be a UUID (ideally version 4).
    """

    def test_status_code_is_400_when_request_id_not_uuid(
        self, stub: PdsFhirApiStub
    ) -> None:
        response = stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id="not-a-uuid"
        )
        assert response.status_code == 400

    def test_no_request_id_format_validation_in_relaxed_mode(
        self, relaxed_stub: PdsFhirApiStub
    ) -> None:
        """In non-strict mode a non-UUID ``X-Request-ID`` does not cause a 400."""
        response = relaxed_stub.get_patient(
            nhs_number=_KNOWN_NHS_NUMBER, request_id="not-a-uuid"
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# OperationOutcome structure (shared across error responses)
# ---------------------------------------------------------------------------


class TestOperationOutcomeStructure:
    """Verify that every error OperationOutcome conforms to the FHIR/PDS structure."""

    @pytest.fixture(
        params=[
            pytest.param((None, _KNOWN_NHS_NUMBER), id="missing_request_id"),
            pytest.param(("not-a-uuid", _KNOWN_NHS_NUMBER), id="invalid_request_id"),
            pytest.param((_VALID_REQUEST_ID, _INVALID_NHS_NUMBER), id="invalid_nhs"),
            pytest.param((_VALID_REQUEST_ID, _UNKNOWN_NHS_NUMBER), id="not_found"),
        ]
    )
    def error_response(
        self, stub: PdsFhirApiStub, request: pytest.FixtureRequest
    ) -> requests.Response:
        request_id, nhs_number = request.param
        return stub.get_patient(nhs_number=nhs_number, request_id=request_id)

    def test_resource_type(self, error_response: requests.Response) -> None:
        body = error_response.json()
        assert body["resourceType"] == "OperationOutcome"

    def test_issue_array_is_present_and_non_empty(
        self, error_response: requests.Response
    ) -> None:
        body = error_response.json()
        assert isinstance(body.get("issue"), list)
        assert len(body["issue"]) >= 1

    def test_issue_has_severity(self, error_response: requests.Response) -> None:
        body = error_response.json()
        issue = body["issue"][0]
        assert "severity" in issue

    def test_issue_has_code(self, error_response: requests.Response) -> None:
        body = error_response.json()
        issue = body["issue"][0]
        assert "code" in issue

    def test_issue_details_coding_system(
        self, error_response: requests.Response
    ) -> None:
        """All errors must use the Spine error code system."""
        body = error_response.json()
        coding = body["issue"][0]["details"]["coding"][0]
        assert (
            coding["system"]
            == "https://fhir.nhs.uk/R4/CodeSystem/Spine-ErrorOrWarningCode"
        )

    def test_issue_details_coding_has_code(
        self, error_response: requests.Response
    ) -> None:
        body = error_response.json()
        coding = body["issue"][0]["details"]["coding"][0]
        assert "code" in coding
        assert coding["code"]  # non-empty

    def test_issue_details_coding_has_display(
        self, error_response: requests.Response
    ) -> None:
        body = error_response.json()
        coding = body["issue"][0]["details"]["coding"][0]
        assert "display" in coding
        assert coding["display"]  # non-empty


# ---------------------------------------------------------------------------
# get() convenience wrapper – delegates correctly to get_patient()
# ---------------------------------------------------------------------------


class TestGetConvenienceMethod:
    """Verify the ``get()`` wrapper passes headers through to ``get_patient()``."""

    def test_get_known_patient_returns_200(self, stub: PdsFhirApiStub) -> None:
        url = f"https://api.service.nhs.uk/personal-demographics/FHIR/R4/Patient/{_KNOWN_NHS_NUMBER}"
        response = stub.get(
            url=url,
            headers={
                "X-Request-ID": _VALID_REQUEST_ID,
            },
        )
        assert response.status_code == 200

    def test_get_without_request_id_returns_400(self, stub: PdsFhirApiStub) -> None:
        url = f"https://api.service.nhs.uk/personal-demographics/FHIR/R4/Patient/{_KNOWN_NHS_NUMBER}"
        response = stub.get(url=url, headers={})
        assert response.status_code == 400

    def test_get_passes_correlation_id(self, stub: PdsFhirApiStub) -> None:
        url = f"https://api.service.nhs.uk/personal-demographics/FHIR/R4/Patient/{_KNOWN_NHS_NUMBER}"
        response = stub.get(
            url=url,
            headers={
                "X-Request-ID": _VALID_REQUEST_ID,
                "X-Correlation-ID": _VALID_CORRELATION_ID,
            },
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID
