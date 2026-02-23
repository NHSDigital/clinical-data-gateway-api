"""
Unit tests for :mod:`gateway_api.pds_search`.
"""

from datetime import date
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import pytest
from fhir import Patient
from pytest_mock import MockerFixture

from gateway_api.common.error import PdsRequestFailedError
from gateway_api.conftest import FakeResponse
from gateway_api.pds.client import PdsClient

if TYPE_CHECKING:
    from fhir import GeneralPractitioner, HumanName


def test_search_patient_by_nhs_number_happy_path(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: Patient,
) -> None:
    happy_path_response = FakeResponse(
        status_code=200, headers={}, _json=happy_path_pds_response_body
    )
    mocker.patch("gateway_api.pds.client.get", return_value=happy_path_response)

    client = PdsClient(auth_token)
    result = client.search_patient_by_nhs_number("9999999999")

    assert result is not None
    assert result.nhs_number == "9999999999"
    assert result.family_name == "Johnson"
    assert result.given_names == "Alice"
    assert result.gp_ods_code == "A12345"


def test_search_patient_by_nhs_number_has_no_gp_returns_gp_ods_code_none(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: Patient,
) -> None:
    gp_less_response_body = happy_path_pds_response_body.copy()
    del gp_less_response_body["generalPractitioner"]
    gp_less_response = FakeResponse(
        status_code=200, headers={}, _json=gp_less_response_body
    )
    mocker.patch("gateway_api.pds.client.get", return_value=gp_less_response)

    client = PdsClient(auth_token)
    result = client.search_patient_by_nhs_number("9999999999")

    assert result is not None
    assert result.nhs_number == "9999999999"
    assert result.family_name == "Johnson"
    assert result.given_names == "Alice"
    assert result.gp_ods_code is None


def test_search_patient_by_nhs_number_sends_expected_headers(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: Patient,
) -> None:
    happy_path_response = FakeResponse(
        status_code=200, headers={}, _json=happy_path_pds_response_body
    )
    mocked_get = mocker.patch(
        "gateway_api.pds.client.get", return_value=happy_path_response
    )

    request_id = str(uuid4())
    correlation_id = "corr-123"

    client = PdsClient(auth_token)
    _ = client.search_patient_by_nhs_number(
        "9000000009",
        request_id=request_id,
        correlation_id=correlation_id,
    )

    expected_headers = {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/fhir+json",
        "X-Request-ID": request_id,
        "X-Correlation-ID": correlation_id,
    }

    assert mocked_get.call_args.kwargs["headers"] == expected_headers


def test_search_patient_by_nhs_number_generates_request_id(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: Patient,
) -> None:
    happy_path_response = FakeResponse(
        status_code=200, headers={}, _json=happy_path_pds_response_body
    )
    mocked_get = mocker.patch(
        "gateway_api.pds.client.get", return_value=happy_path_response
    )

    client = PdsClient(auth_token)

    _ = client.search_patient_by_nhs_number("9000000009")

    try:
        _ = UUID(mocked_get.call_args.kwargs["headers"]["X-Request-ID"], version=4)
    except ValueError:
        pytest.fail("X-Request-ID is not a valid UUID4")


def test_search_patient_by_nhs_number_not_found_raises_error(
    auth_token: str,
    mocker: MockerFixture,
) -> None:
    not_found_response = FakeResponse(
        status_code=404,
        headers={},
        _json={"resourceType": "OperationOutcome", "issue": []},
        reason="Not Found",
    )
    mocker.patch("gateway_api.pds.client.get", return_value=not_found_response)
    pds = PdsClient(auth_token)

    with pytest.raises(
        PdsRequestFailedError, match="PDS FHIR API request failed: Not Found"
    ):
        pds.search_patient_by_nhs_number("9900000001")


def test_search_patient_by_nhs_number_finds_current_gp_ods_code_when_pds_returns_two(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: Patient,
) -> None:
    old_gp: GeneralPractitioner = {
        "id": "1",
        "type": "Organization",
        "identifier": {
            "value": "OLDGP",
            "period": {"start": "2010-01-01", "end": "2012-01-01"},
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
        },
    }
    current_gp: GeneralPractitioner = {
        "id": "2",
        "type": "Organization",
        "identifier": {
            "value": "CURRGP",
            "period": {"start": "2020-01-01", "end": "9999-01-01"},
            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
        },
    }
    pds_response_body_with_two_gps = happy_path_pds_response_body.copy()
    pds_response_body_with_two_gps["generalPractitioner"] = [old_gp, current_gp]
    pds_response_with_two_gps = FakeResponse(
        status_code=200, headers={}, _json=pds_response_body_with_two_gps
    )
    mocker.patch("gateway_api.pds.client.get", return_value=pds_response_with_two_gps)

    client = PdsClient(auth_token)

    result = client.search_patient_by_nhs_number("9999999999")
    assert result is not None
    assert result.nhs_number == "9999999999"
    assert result.family_name == "Johnson"
    assert result.given_names == "Alice"
    assert result.gp_ods_code == "CURRGP"


def test_find_current_gp_with_today_override() -> None:
    """
    Verify that ``find_current_gp`` honours an explicit ``today`` value.
    """
    pds = PdsClient("test-token", "A12345")
    pds_ignore_dates = PdsClient("test-token", "A12345", ignore_dates=True)

    records: list[GeneralPractitioner] = [
        {
            "id": "1234",
            "type": "Organization",
            "identifier": {
                "value": "a",
                "period": {"start": "2020-01-01", "end": "2020-12-31"},
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            },
        },
        {
            "id": "abcd",
            "type": "Organization",
            "identifier": {
                "value": "b",
                "period": {"start": "2021-01-01", "end": "2021-12-31"},
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            },
        },
    ]

    assert pds.find_current_gp(records, today=date(2020, 6, 1)) == records[0]
    assert pds.find_current_gp(records, today=date(2021, 6, 1)) == records[1]
    assert pds.find_current_gp(records, today=date(2019, 6, 1)) is None
    assert pds_ignore_dates.find_current_gp(records, today=date(2019, 6, 1)) is not None


def test_find_current_name_record_no_current_name() -> None:
    """
    Verify that ``find_current_name_record`` returns ``None`` when no current name
    exists.
    """
    pds = PdsClient("test-token", "A12345")
    pds_ignore_date = PdsClient("test-token", "A12345", ignore_dates=True)

    records: list[HumanName] = [
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
    ]

    assert pds.find_current_name_record(records) is None
    assert pds_ignore_date.find_current_name_record(records) is not None


def test_extract_single_search_result_with_invalid_body_raises_pds_request_failed() -> (
    None
):
    """
    Verify that ``PdsClient._extract_single_search_result`` raises ``PdsRequestFailed``
    when mandatory patient content is missing.

    This test asserts that a ``PdsRequestFailed`` is raised when:

    * The body is a bundle containing no entries (``entry`` is empty).
    * The body is a patient resource with no NHS number (missing/blank ``id``).
    * The body is a patient resource with an NHS number,
        but the patient has no *current* name record.
    """
    client = PdsClient(
        auth_token="test-token",  # noqa: S106 (test token hardcoded)
        base_url="https://example.test/personal-demographics/FHIR/R4",
    )

    # 1) Bundle contains no entries.
    bundle_no_entries: Any = {"resourceType": "Bundle", "entry": []}
    with pytest.raises(PdsRequestFailedError):
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
    with pytest.raises(PdsRequestFailedError):
        client._extract_single_search_result(patient_missing_nhs_number)  # noqa SLF001 (testing private method)

    # 3) Bundle entry exists with NHS number, but no current name record.
    bundle_no_current_name: Any = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
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
            }
        ],
    }

    # No current name record is tolerated by PdsClient; names are returned as empty.
    result = client._extract_single_search_result(bundle_no_current_name)  # noqa SLF001 (testing private method)
    assert result is not None
    assert result.nhs_number == "9000000009"
    assert result.given_names == ""
    assert result.family_name == ""


def test_find_current_name_record_ignore_dates_returns_last_or_none() -> None:
    """
    If ignore_dates=True:
    * returns the last name record even if none are current
    * returns None when the list is empty
    """
    pds_ignore = PdsClient("test-token", "A12345", ignore_dates=True)

    records: list[HumanName] = [
        {
            "use": "official",
            "family": "Old",
            "given": ["First"],
            "period": {"start": "1900-01-01", "end": "1900-12-31"},
        },
        {
            "use": "official",
            "family": "Newer",
            "given": ["Second"],
            "period": {"start": "1901-01-01", "end": "1901-12-31"},
        },
    ]

    # Pick a date that is not covered by any record; ignore_dates should still pick last
    chosen = pds_ignore.find_current_name_record(records, today=date(2026, 1, 1))
    assert chosen == records[-1]

    assert pds_ignore.find_current_name_record([]) is None


def test_find_current_gp_ignore_dates_returns_last_or_none() -> None:
    """
    If ignore_dates=True:
    * returns the last GP record even if none are current
    * returns None when the list is empty
    """
    pds_ignore = PdsClient("test-token", "A12345", ignore_dates=True)

    records: list[GeneralPractitioner] = [
        {
            "id": "abcd",
            "type": "Organization",
            "identifier": {
                "value": "GP-OLD",
                "period": {"start": "1900-01-01", "end": "1900-12-31"},
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            },
        },
        {
            "id": "1234",
            "type": "Organization",
            "identifier": {
                "value": "GP-NEWER",
                "period": {"start": "1901-01-01", "end": "1901-12-31"},
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
            },
        },
    ]

    # Pick a date that is not covered by any record; ignore_dates should still pick last
    chosen = pds_ignore.find_current_gp(records, today=date(2026, 1, 1))
    assert chosen == records[-1]

    assert pds_ignore.find_current_gp([]) is None
