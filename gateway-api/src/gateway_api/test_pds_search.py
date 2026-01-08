"""
Unit tests for :mod:`gateway_api.pds_search`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, cast
from uuid import uuid4

import pytest
import requests
from stubs.stub_pds import PdsFhirApiStub

from gateway_api.pds_search import (
    ExternalServiceError,
    PdsClient,
    ResultList,
    find_current_gp,
    find_current_name_record,
)


@dataclass
class FakeResponse:
    """
    Minimal substitute for :class:`requests.Response` used by tests.

    Only the methods accessed by :class:`gateway_api.pds_search.PdsClient` are
    implemented.

    :param status_code: HTTP status code.
    :param headers: Response headers.
    :param _json: Parsed JSON body returned by :meth:`json`.
    """

    status_code: int
    headers: dict[str, str]
    _json: dict[str, Any]

    def json(self) -> dict[str, Any]:
        """
        Return the response JSON body.

        :return: Parsed JSON body.
        """
        return self._json

    def raise_for_status(self) -> None:
        """
        Emulate :meth:`requests.Response.raise_for_status`.

        :return: ``None``.
        :raises requests.HTTPError: If the response status is not 200.
        """
        if self.status_code != 200:
            raise requests.HTTPError(f"{self.status_code} Error")


@pytest.fixture
def stub() -> PdsFhirApiStub:
    """
    Create a stub backend instance.

    :return: A :class:`stubs.stub_pds.PdsFhirApiStub` with strict header validation
        enabled.
    """
    # Strict header validation helps ensure PdsClient sends X-Request-ID correctly.
    return PdsFhirApiStub(strict_headers=True)


@pytest.fixture
def mock_requests_get(
    monkeypatch: pytest.MonkeyPatch, stub: PdsFhirApiStub
) -> dict[str, Any]:
    """
    Patch ``requests.get`` so calls are routed into :meth:`PdsFhirApiStub.get_patient`.

    The fixture returns a "capture" dict recording the most recent request information.
    This is used by header-related tests.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param stub: Stub backend used to serve GET requests.
    :return: A capture dictionary containing the last call details
        (url/headers/params/timeout).
    """
    capture: dict[str, Any] = {}

    def _fake_get(
        url: str,
        headers: dict[str, str] | None = None,
        params: Any = None,
        timeout: Any = None,
    ) -> FakeResponse:
        """
        Replacement function for :func:`requests.get`.

        :param url: URL passed by the client.
        :param headers: Headers passed by the client.
        :param params: Query parameters (recorded, not interpreted for
            GET /Patient/{id}).
        :param timeout: Timeout (recorded).
        :return: A :class:`FakeResponse` whose behaviour mimics ``requests.Response``.
        """
        headers = headers or {}
        capture["url"] = url
        capture["headers"] = dict(headers)
        capture["params"] = params
        capture["timeout"] = timeout

        # The client under test is expected to call GET {base_url}/Patient/{id}.
        m = re.match(r"^(?P<base>.+)/Patient/(?P<nhs>\d+)$", url)
        if not m:
            raise AssertionError(f"Unexpected URL called by client: {url}")

        nhs_number = m.group("nhs")

        # Route the "HTTP" request into the in-memory stub.
        stub_resp = stub.get_patient(
            nhs_number=nhs_number,
            request_id=headers.get("X-Request-ID"),
            correlation_id=headers.get("X-Correlation-ID"),
            authorization=headers.get("Authorization"),
            end_user_org_ods=headers.get("NHSD-End-User-Organisation-ODS"),
        )

        # GET /Patient/{id} returns a single Patient resource on success.
        body = stub_resp.json

        return FakeResponse(
            status_code=stub_resp.status_code, headers=stub_resp.headers, _json=body
        )

    monkeypatch.setattr(requests, "get", _fake_get)
    return capture


def _insert_basic_patient(
    stub: PdsFhirApiStub,
    nhs_number: str,
    family: str,
    given: list[str],
    general_practitioner: list[dict[str, Any]] | None = None,
) -> None:
    """
    Insert a basic Patient record into the stub.

    :param stub: Stub backend to insert into.
    :param nhs_number: NHS number (10-digit string).
    :param family: Family name for the Patient.name record.
    :param given: Given names for the Patient.name record.
    :param general_practitioner: Optional list stored under
        ``Patient.generalPractitioner``.
    :return: ``None``.
    """
    stub.upsert_patient(
        nhs_number=nhs_number,
        patient={
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": family,
                    "given": given,
                    "period": {"start": "1900-01-01", "end": "9999-12-31"},
                }
            ],
            "generalPractitioner": general_practitioner or [],
        },
        version_id=1,
    )


def test_search_patient_by_nhs_number_get_patient_success(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify ``GET /Patient/{nhs_number}`` returns 200 and demographics are extracted.

    This test explicitly inserts the patient into the stub and asserts that the client
    returns a populated :class:`gateway_api.pds_search.SearchResults`.

    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture
        (ensures patching is active).
    :return: ``None``.
    """
    _insert_basic_patient(
        stub=stub,
        nhs_number="9000000009",
        family="Smith",
        given=["Jane"],
        general_practitioner=[],
    )

    client = PdsClient(
        auth_token="test-token",  # noqa: S106  (test token hardcoded)
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
        nhsd_session_urid="test-urid",
    )

    result = client.search_patient_by_nhs_number(9000000009)

    assert result is not None
    assert result.nhs_number == "9000000009"
    assert result.family_name == "Smith"
    assert result.given_names == "Jane"
    assert result.gp_ods_code is None


def test_search_patient_by_nhs_number_no_current_gp_returns_gp_ods_code_none(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify that ``gp_ods_code`` is ``None`` when no GP record is current.

    The generalPractitioner list may be:
    * empty
    * non-empty with no current record
    * non-empty with exactly one current record

    This test covers the "non-empty, none current" case by
    inserting only a historical GP record.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture.
    :return: ``None``.
    """
    _insert_basic_patient(
        stub=stub,
        nhs_number="9000000018",
        family="Taylor",
        given=["Ben"],
        general_practitioner=[
            {
                "id": "1",
                "type": "Organization",
                "identifier": {
                    "value": "OLDGP",
                    "period": {"start": "2010-01-01", "end": "2012-01-01"},
                },
            }
        ],
    )

    client = PdsClient(
        auth_token="test-token",  # noqa: S106  (test token hardcoded)
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000018)

    assert result is not None
    assert result.nhs_number == "9000000018"
    assert result.family_name == "Taylor"
    assert result.given_names == "Ben"
    assert result.gp_ods_code is None


def test_search_patient_by_nhs_number_sends_expected_headers(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify that the client sends the expected headers to PDS.

    Asserts that the request contains:
    * Authorization header
    * NHSD-End-User-Organisation-ODS header
    * Accept header
    * caller-provided X-Request-ID and X-Correlation-ID headers

    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture capturing outbound
        headers.
    :return: ``None``.
    """
    _insert_basic_patient(
        stub=stub,
        nhs_number="9000000009",
        family="Smith",
        given=["Jane"],
        general_practitioner=[],
    )

    client = PdsClient(
        auth_token="test-token",  # noqa: S106
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    req_id = str(uuid4())
    corr_id = "corr-123"

    result = client.search_patient_by_nhs_number(
        9000000009,
        request_id=req_id,
        correlation_id=corr_id,
    )
    assert result is not None

    headers = mock_requests_get["headers"]
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["NHSD-End-User-Organisation-ODS"] == "A12345"
    assert headers["Accept"] == "application/fhir+json"
    assert headers["X-Request-ID"] == req_id
    assert headers["X-Correlation-ID"] == corr_id


def test_search_patient_by_nhs_number_generates_request_id(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify that the client generates an X-Request-ID when not provided.

    The stub is in strict mode, so a missing or invalid X-Request-ID would cause a 400.
    This test confirms a request ID is present and looks UUID-like.

    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture capturing outbound
        headers.
    :return: ``None``.
    """
    _insert_basic_patient(
        stub=stub,
        nhs_number="9000000009",
        family="Smith",
        given=["Jane"],
        general_practitioner=[],
    )

    client = PdsClient(
        auth_token="test-token",  # noqa: S106
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000009)
    assert result is not None

    headers = mock_requests_get["headers"]
    assert "X-Request-ID" in headers
    assert isinstance(headers["X-Request-ID"], str)
    assert len(headers["X-Request-ID"]) >= 32


def test_search_patient_by_nhs_number_not_found_raises_error(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify that a 404 response results in :class:`ExternalServiceError`.

    The stub returns a 404 OperationOutcome for unknown NHS numbers. The client calls
    ``raise_for_status()``, which raises ``requests.HTTPError``; the client wraps that
    into :class:`ExternalServiceError`.

    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture.
    :return: ``None``.
    """
    pds = PdsClient(
        auth_token="test-token",  # noqa: S106
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    with pytest.raises(ExternalServiceError):
        pds.search_patient_by_nhs_number(9900000001)


def test_search_patient_by_nhs_number_extracts_current_gp_ods_code(
    stub: PdsFhirApiStub,
    mock_requests_get: dict[str, Any],
) -> None:
    """
    Verify that a current GP record is selected and its ODS code returned.

    The test inserts a patient with two GP records:
    * one historical (not current)
    * one current (period covers today)

    :param monkeypatch: Pytest monkeypatch fixture.
    :param stub: Stub backend fixture.
    :param mock_requests_get: Patched ``requests.get`` fixture.
    :return: ``None``.
    """
    stub.upsert_patient(
        nhs_number="9000000017",
        patient={
            "resourceType": "Patient",
            "name": [
                {
                    "use": "official",
                    "family": "Taylor",
                    "given": ["Ben", "A."],
                    "period": {"start": "1900-01-01", "end": "9999-12-31"},
                }
            ],
            "generalPractitioner": [
                # Old
                {
                    "id": "1",
                    "type": "Organization",
                    "identifier": {
                        "value": "OLDGP",
                        "period": {"start": "2010-01-01", "end": "2012-01-01"},
                    },
                },
                # Current
                {
                    "id": "2",
                    "type": "Organization",
                    "identifier": {
                        "value": "CURRGP",
                        "period": {"start": "2020-01-01", "end": "9999-01-01"},
                    },
                },
            ],
        },
        version_id=1,
    )

    client = PdsClient(
        auth_token="test-token",  # noqa: S106
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000017)
    assert result is not None
    assert result.nhs_number == "9000000017"
    assert result.family_name == "Taylor"
    assert result.given_names == "Ben A."
    assert result.gp_ods_code == "CURRGP"


def test_find_current_gp_with_today_override() -> None:
    """
    Verify that ``find_current_gp`` honours an explicit ``today`` value.

    :return: ``None``.
    """
    records = cast(
        "ResultList",
        [
            {
                "identifier": {
                    "value": "a",
                    "period": {"start": "2020-01-01", "end": "2020-12-31"},
                }
            },
            {
                "identifier": {
                    "value": "b",
                    "period": {"start": "2021-01-01", "end": "2021-12-31"},
                }
            },
        ],
    )

    assert find_current_gp(records, today=date(2020, 6, 1)) == records[0]
    assert find_current_gp(records, today=date(2021, 6, 1)) == records[1]
    assert find_current_gp(records, today=date(2019, 6, 1)) is None


def test_find_current_name_record_no_current_name() -> None:
    """
    Verify that ``find_current_name_record`` returns ``None`` when no current name
    exists.

    :return: ``None``.
    """
    records = cast(
        "ResultList",
        [
            {
                "use": "official",
                "family": "Doe",
                "given": ["John"],
                "period": {"start": "2000-01-01", "end": "2010-12-31"},
            },
            {
                "use": "official",
                "family": "Smith",
                "given": ["John"],
                "period": {"start": "2011-01-01", "end": "2020-12-31"},
            },
        ],
    )

    assert find_current_name_record(records) is None


def test_extract_single_search_result_invalid_body_raises_runtime_error() -> None:
    """
    Verify that ``PdsClient._extract_single_search_result`` raises ``RuntimeError`` when
    mandatory patient content is missing.

    This test asserts that a ``RuntimeError`` is raised when:

    * The body is a bundle containing no entries (``entry`` is empty).
    * The body is a patient resource with no NHS number (missing/blank ``id``).
    * The body is a patient resource with an NHS number,
        but the patient has no *current*
    """
    client = PdsClient(
        auth_token="test-token",  # noqa: S106 (test token hardcoded)
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    # 1) Bundle contains no entries.
    bundle_no_entries: Any = {"resourceType": "Bundle", "entry": []}
    with pytest.raises(RuntimeError):
        client._extract_single_search_result(bundle_no_entries)  # noqa SLF001 (testing private method)

    # 2) Patient has no NHS number (Patient.id missing/blank).
    patient_missing_nhs_number: Any = {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["Jane"],
                "period": {"start": "1900-01-01", "end": "9999-12-31"},
            }
        ],
        "generalPractitioner": [],
    }
    with pytest.raises(RuntimeError):
        client._extract_single_search_result(patient_missing_nhs_number)  # noqa SLF001 (testing private method)

    # 3) Patient has NHS number, but no current name record.
    patient_no_current_name: Any = {
        "resourceType": "Patient",
        "id": "9000000009",
        "name": [
            {
                "use": "official",
                "family": "Smith",
                "given": ["Jane"],
                "period": {"start": "1900-01-01", "end": "1900-12-31"},
            }
        ],
        "generalPractitioner": [],
    }

    with pytest.raises(RuntimeError):
        client._extract_single_search_result(patient_no_current_name)  # noqa SLF001 (testing private method)
