# tests/test_pds_search.py
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone, tzinfo
from typing import Any, cast
from uuid import uuid4

import pytest
import requests
from stubs.stub_pds import PdsFhirApiStub

import gateway_api.pds_search as pds_search
from gateway_api.pds_search import PdsSearch, ResultList, find_current_record


@dataclass
class FakeResponse:
    status_code: int
    headers: dict[str, str]
    _json: dict[str, Any]

    def json(self) -> dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> FrozenDateTime:
        return cast(
            "FrozenDateTime", datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        )


@pytest.fixture
def stub() -> PdsFhirApiStub:
    # Strict header validation helps ensure PdsSearch sends X-Request-ID correctly.
    return PdsFhirApiStub(strict_headers=True)


@pytest.fixture
def route_requests_get(
    monkeypatch: pytest.MonkeyPatch, stub: PdsFhirApiStub
) -> dict[str, Any]:
    """
    Patch requests.get so that calls made by PdsSearch are routed into the stub.

    Returns a capture dict that records the last request made.
    """
    capture: dict[str, Any] = {}

    def _fake_get(
        url: str,
        headers: dict[str, str] | None = None,
        params: Any = None,
        timeout: Any = None,
    ) -> FakeResponse:
        headers = headers or {}
        capture["url"] = url
        capture["headers"] = dict(headers)
        capture["params"] = params
        capture["timeout"] = timeout

        # Support only GET /Patient/{id} (as used by search_patient_by_nhs_number).
        m = re.match(r"^(?P<base>.+)/Patient/(?P<nhs>\d+)$", url)
        if not m:
            raise AssertionError(f"Unexpected URL called by client: {url}")

        nhs_number = m.group("nhs")

        stub_resp = stub.get_patient(
            nhs_number=nhs_number,
            request_id=headers.get("X-Request-ID"),
            correlation_id=headers.get("X-Correlation-ID"),
            authorization=headers.get("Authorization"),
            end_user_org_ods=headers.get("NHSD-End-User-Organisation-ODS"),
        )

        # pds_search.PdsSearch._extract_single_search_result expects a Bundle-like
        # structure: {"entry": [{"resource": {...Patient...}}]}
        if stub_resp.status_code == 200:
            body = {"entry": [{"resource": stub_resp.json}]}
        else:
            body = stub_resp.json

        return FakeResponse(
            status_code=stub_resp.status_code, headers=stub_resp.headers, _json=body
        )

    monkeypatch.setattr(requests, "get", _fake_get)
    return capture


def test_search_patient_by_nhs_number_success_defaults(
    route_requests_get: dict[str, Any],
) -> None:
    """
    Verifies that a successful GET /Patient/{nhs_number} returns a parsed SearchResults
    populated from the stubbed seeded patient, and that gp_ods_code is None when no
    current generalPractitioner record exists.
    """
    client = PdsSearch(
        auth_token="test-token",  # noqa S106 # test token hardcoded
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000009)

    assert result is not None
    assert result.nhs_number == "9000000009"
    assert result.family_name == "Smith"
    assert result.given_names == "Jane"
    assert result.gp_ods_code is None  # default seeded patient has no GP in stub


def test_search_patient_by_nhs_number_sends_expected_headers(
    route_requests_get: dict[str, Any],
) -> None:
    """
    Verifies that search_patient_by_nhs_number forwards the expected HTTP headers,
    including Authorization, end-user ODS header, Accept, and caller-provided
    X-Request-ID / X-Correlation-ID values.
    """
    client = PdsSearch(
        auth_token="test-token",  # noqa S106 # test token hardcoded
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

    headers = route_requests_get["headers"]
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["NHSD-End-User-Organisation-ODS"] == "A12345"
    assert headers["Accept"] == "application/fhir+json"
    assert headers["X-Request-ID"] == req_id
    assert headers["X-Correlation-ID"] == corr_id


def test_search_patient_by_nhs_number_generates_request_id(
    route_requests_get: dict[str, Any],
) -> None:
    """
    Verifies that when no request_id is provided by the caller, PdsSearch generates
    an X-Request-ID and includes it in the outbound request (the stub validates the
    header format in strict mode).
    """
    client = PdsSearch(
        auth_token="test-token",  # noqa S106 # test token hardcoded
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000009)
    assert result is not None

    # Ensure client generated an X-Request-ID (stub validates UUID shape in strict mode)
    headers = route_requests_get["headers"]
    assert "X-Request-ID" in headers
    # A light sanity check; strict validation is performed inside the stub.
    assert isinstance(headers["X-Request-ID"], str)
    assert len(headers["X-Request-ID"]) >= 32


def test_search_patient_by_nhs_number_not_found_returns_none(
    stub: PdsFhirApiStub,
    route_requests_get: dict[str, Any],
) -> None:
    """
    Verifies that when the downstream PDS endpoint returns 404 (patient not found),
    the client handles the HTTP error path and returns None rather than propagating
    an exception to the caller.
    """
    client = PdsSearch(
        auth_token="test-token",  # noqa S106 # test token hardcoded
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    # Not seeded into stub store => 404 => raise_for_status => client returns None.
    result = client.search_patient_by_nhs_number(9999999999)
    assert result is None


def test_search_patient_by_nhs_number_extracts_current_gp_ods_code(
    monkeypatch: pytest.MonkeyPatch,
    stub: PdsFhirApiStub,
    route_requests_get: dict[str, Any],
) -> None:
    """
    Verifies that gp_ods_code is extracted from the *current* generalPractitioner
    record, where "current" is determined by identifier.period covering today's
    date. Time is frozen via monkeypatch to ensure deterministic selection.
    """
    monkeypatch.setattr(pds_search, "datetime", FrozenDateTime)

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
                # Not current on 2026-01-02
                {
                    "id": "1",
                    "type": "Organization",
                    "identifier": {
                        "value": "OLDGP",
                        "period": {"start": "2010-01-01", "end": "2012-01-01"},
                    },
                },
                # Current on 2026-01-02
                {
                    "id": "2",
                    "type": "Organization",
                    "identifier": {
                        "value": "CURRGP",
                        "period": {"start": "2020-01-01", "end": "2030-01-01"},
                    },
                },
            ],
        },
        version_id=1,
    )

    client = PdsSearch(
        auth_token="test-token",  # noqa S106 # test token hardcoded
        end_user_org_ods="A12345",
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    result = client.search_patient_by_nhs_number(9000000017)
    assert result is not None
    assert result.nhs_number == "9000000017"
    assert result.family_name == "Taylor"
    assert result.given_names == "Ben A."
    assert result.gp_ods_code == "CURRGP"


def test_find_current_record_with_today_override() -> None:
    """
    Verifies that find_current_record honours the explicit `today` override and
    selects the first record whose identifier.period covers that date, returning
    None when no record is current for the supplied date.
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

    assert find_current_record(records, today=date(2020, 6, 1)) == records[0]
    assert find_current_record(records, today=date(2021, 6, 1)) == records[1]
    assert find_current_record(records, today=date(2019, 6, 1)) is None
