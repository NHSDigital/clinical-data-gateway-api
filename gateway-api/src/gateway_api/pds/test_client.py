"""
Unit tests for :mod:`gateway_api.pds_search`.
"""

from typing import Any
from uuid import UUID, uuid4

import pytest
from fhir.resources import Patient
from pytest_mock import MockerFixture

from gateway_api.common.error import PdsRequestFailedError
from gateway_api.conftest import FakeResponse
from gateway_api.pds.client import PdsClient


def test_search_patient_by_nhs_number_happy_path(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: dict[str, Any],
) -> None:
    happy_path_response = FakeResponse(
        status_code=200, headers={}, _json=happy_path_pds_response_body
    )
    mocker.patch("gateway_api.pds.client.get", return_value=happy_path_response)

    client = PdsClient(auth_token)
    result = client.search_patient_by_nhs_number("9999999999")

    assert isinstance(result, Patient)
    assert result.nhs_number == "9999999999"
    assert result.gp_ods_code == "A12345"


def test_search_patient_by_nhs_number_has_no_gp_returns_gp_ods_code_none(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: dict[str, Any],
) -> None:
    gp_less_response_body = happy_path_pds_response_body.copy()
    del gp_less_response_body["generalPractitioner"]
    gp_less_response = FakeResponse(
        status_code=200, headers={}, _json=gp_less_response_body
    )
    mocker.patch("gateway_api.pds.client.get", return_value=gp_less_response)

    client = PdsClient(auth_token)
    result = client.search_patient_by_nhs_number("9999999999")

    assert isinstance(result, Patient)
    assert result.nhs_number == "9999999999"
    assert result.gp_ods_code is None


def test_search_patient_by_nhs_number_sends_expected_headers(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: dict[str, Any],
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
    happy_path_pds_response_body: dict[str, Any],
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


def test_search_patient_by_nhs_number_missing_nhs_number_raises_error(
    auth_token: str,
    mocker: MockerFixture,
    happy_path_pds_response_body: dict[str, Any],
) -> None:
    response_body_missing_nhs_number = happy_path_pds_response_body.copy()
    response_body_missing_nhs_number["identifier"] = []

    response = FakeResponse(
        status_code=200,
        headers={},
        _json=response_body_missing_nhs_number,
    )
    mocker.patch("gateway_api.pds.client.get", return_value=response)

    client = PdsClient(auth_token)

    with pytest.raises(
        PdsRequestFailedError,
        match="PDS FHIR API request failed: PDS Patient resource missing NHS number",
    ):
        client.search_patient_by_nhs_number("9999999999")
