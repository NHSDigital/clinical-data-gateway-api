"""Unit tests for :mod:`gateway_api.controller`."""

from typing import Any
from unittest.mock import Mock

import pytest
from fhir.r4 import (
    GeneralPractitioner,
    OrganizationIdentifier,
    Patient,
    PatientIdentifier,
)
from flask import Request
from pytest_mock import MockerFixture

from gateway_api.common.error import (
    NoAsidFoundError,
    NoCurrentEndpointError,
    NoCurrentProviderError,
    NoOrganisationFoundError,
)
from gateway_api.conftest import FakeResponse, create_mock_request
from gateway_api.controller import Controller
from gateway_api.get_structured_record import GetStructuredRecordRequest
from gateway_api.sds import SdsSearchResults


@pytest.fixture
def mock_flask() -> Mock:
    mock_flask = Mock()
    mock_flask.config = {"SDS_API_TOKEN": "example"}
    return mock_flask


def _create_patient(nhs_number: str, gp_ods_code: str | None) -> Patient:
    general_practitioner = None
    if gp_ods_code is not None:
        general_practitioner = [
            GeneralPractitioner(
                type="Organization",
                identifier=OrganizationIdentifier(
                    value=gp_ods_code,
                ),
            )
        ]

    return Patient.create(
        identifier=[PatientIdentifier.from_nhs_number(nhs_number)],
        generalPractitioner=general_practitioner,
    )


def create_test_controller(
    pds_base_url: str = "https://example.test/pds",
    sds_base_url: str = "https://example.test/sds",
    sds_api_key: str = "example_sds_api_key",
) -> Controller:
    return Controller(
        pds_base_url=pds_base_url,
        sds_base_url=sds_base_url,
        sds_api_key=sds_api_key,
    )


def test_controller_run_happy_path_returns_200_status_code(
    mock_happy_path_get_structured_record_request: Request,
) -> None:
    request = GetStructuredRecordRequest(mock_happy_path_get_structured_record_request)

    controller = create_test_controller()
    actual_response = controller.run(request)

    assert actual_response.status_code == 200


def test_controller_run_happy_path_returns_returns_expected_body(
    mock_happy_path_get_structured_record_request: Request,
    valid_simple_response_payload: dict[str, Any],
) -> None:
    request = GetStructuredRecordRequest(mock_happy_path_get_structured_record_request)

    controller = create_test_controller()
    actual_response = controller.run(request)

    assert actual_response.json() == valid_simple_response_payload


def test_get_pds_details_returns_provider_ods_code_for_happy_path(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    nhs_number = "9000000009"
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=_create_patient(nhs_number, "A12345"),
    )
    controller = create_test_controller()

    actual = controller._get_pds_details(auth_token, nhs_number)  # noqa: SLF001 testing private method

    assert actual == "A12345"


def test_get_pds_details_raises_no_current_provider_when_ods_code_missing_in_pds(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    nhs_number = "9000000009"
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=_create_patient(nhs_number, None),
    )

    controller = create_test_controller()

    with pytest.raises(
        NoCurrentProviderError,
        match="PDS patient 9000000009 did not contain a current provider ODS code",
    ):
        _ = controller._get_pds_details(auth_token, nhs_number)  # noqa: SLF001 testing private method


def test_get_sds_details_returns_consumer_and_provider_details_for_happy_path(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    provider_sds_results = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    consumer_ods = "ConsumerODS"
    consumer_sds_results = SdsSearchResults(
        asid="ConsumerASID", endpoint="https://example.consumer.org/endpoint"
    )
    sds_results = [provider_sds_results, consumer_sds_results]
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=sds_results,
    )

    controller = create_test_controller()

    expected = ("ConsumerASID", "ProviderASID", "https://example.provider.org/endpoint")
    actual = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method
    assert actual == expected


def test_get_sds_details_raises_no_organisation_found_when_sds_returns_none(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"
    no_results_for_provider = SdsSearchResults(asid=None, endpoint=None)
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        return_value=no_results_for_provider,
    )

    controller = create_test_controller()

    with pytest.raises(
        NoOrganisationFoundError,
        match="No SDS org found for provider ODS code ProviderODS",
    ):
        _ = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method


def test_get_sds_details_raises_no_asid_found_when_sds_returns_empty_asid(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"
    blank_asid_sds_result = SdsSearchResults(
        asid="   ", endpoint="https://example.provider.org/endpoint"
    )
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        return_value=blank_asid_sds_result,
    )

    controller = create_test_controller()

    with pytest.raises(
        NoAsidFoundError,
        match=(
            "SDS result for provider ODS code ProviderODS did not contain "
            "a current ASID"
        ),
    ):
        _ = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method


def test_get_sds_details_raises_no_current_endpoint_when_sds_returns_empty_endpoint(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"
    blank_endpoint_sds_result = SdsSearchResults(asid="ProviderASID", endpoint="   ")
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        return_value=blank_endpoint_sds_result,
    )

    controller = create_test_controller()

    with pytest.raises(
        NoCurrentEndpointError,
        match=(
            "SDS result for provider ODS code ProviderODS did "
            "not contain a current endpoint"
        ),
    ):
        _ = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method


def test_get_sds_details_raises_no_org_found_when_sds_returns_none_for_consumer(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"

    happy_path_provider_sds_result = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    none_result_for_consumer = SdsSearchResults(asid=None, endpoint=None)
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=[happy_path_provider_sds_result, none_result_for_consumer],
    )

    controller = create_test_controller()

    with pytest.raises(
        NoOrganisationFoundError,
        match="No SDS org found for consumer ODS code ConsumerODS",
    ):
        _ = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method


def test_get_sds_details_raises_no_asid_found_when_sds_returns_empty_consumer_asid(
    mocker: MockerFixture,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"

    happy_path_provider_sds_result = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    consumer_asid_blank_sds_result = SdsSearchResults(
        asid="   ", endpoint="https://example.consumer.org/endpoint"
    )
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=[happy_path_provider_sds_result, consumer_asid_blank_sds_result],
    )

    controller = create_test_controller()

    with pytest.raises(
        NoAsidFoundError,
        match=(
            "SDS result for consumer ODS code ConsumerODS did not contain "
            "a current ASID"
        ),
    ):
        _ = controller._get_sds_details(consumer_ods, provider_ods)  # noqa: SLF001 testing private method


@pytest.fixture
def mock_happy_path_get_structured_record_request(
    mocker: MockerFixture,
    valid_simple_request_payload: dict[str, Any],
    valid_simple_response_payload: dict[str, Any],
) -> Request:
    nhs_number = "9000000009"
    provider_ods = "ProviderODS"
    provider_sds_results = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    consumer_ods = "ConsumerODS"
    consumer_sds_results = SdsSearchResults(
        asid="ConsumerASID", endpoint="https://example.consumer.org/endpoint"
    )
    sds_results = [provider_sds_results, consumer_sds_results]
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=_create_patient(nhs_number, provider_ods),
    )
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=sds_results,
    )

    provider_response = FakeResponse(
        status_code=200,
        headers={"Content-Type": "application/fhir+json"},
        _json=valid_simple_response_payload,
    )
    mocker.patch(
        "gateway_api.provider.GpProviderClient.access_structured_record",
        return_value=provider_response,
    )

    happy_path_request = create_mock_request(
        headers={"ODS-From": consumer_ods, "Ssp-TraceID": "test-trace-id"},
        body=valid_simple_request_payload,
    )
    return happy_path_request


def test_controller_creates_jwt_token_with_correct_claims(
    mocker: MockerFixture,
    valid_simple_request_payload: dict[str, Any],
    valid_simple_response_payload: dict[str, Any],
) -> None:
    """
    Test that the controller creates a JWT token with the correct claims.
    """
    nhs_number = "9000000009"
    provider_ods = "PROVIDER"
    consumer_ods = "CONSUMER"
    provider_endpoint = "https://provider.example/ep"

    # Mock PDS to return provider ODS code
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=_create_patient(nhs_number, provider_ods),
    )

    # Mock SDS to return provider and consumer details
    provider_sds_results = SdsSearchResults(
        asid="asid_PROV", endpoint=provider_endpoint
    )
    consumer_sds_results = SdsSearchResults(asid="asid_CONS", endpoint=None)
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=[provider_sds_results, consumer_sds_results],
    )

    # Mock GpProviderClient to capture initialization arguments
    mock_gp_provider = mocker.patch("gateway_api.controller.GpProviderClient")

    # Mock the access_structured_record method to return a response
    provider_response = FakeResponse(
        status_code=200,
        headers={"Content-Type": "application/fhir+json"},
        _json=valid_simple_response_payload,
    )
    mock_gp_provider.return_value.access_structured_record.return_value = (
        provider_response
    )

    # Create request and run controller
    request = create_mock_request(
        headers={"ODS-From": consumer_ods, "Ssp-TraceID": "test-trace-id"},
        body=valid_simple_request_payload,
    )

    get_structured_record_request = GetStructuredRecordRequest(request)

    controller = create_test_controller()
    controller.run(get_structured_record_request)

    # Verify that GpProviderClient was called and extract the JWT token
    mock_gp_provider.assert_called_once()
    jwt_token = mock_gp_provider.call_args.kwargs["token"]

    # Verify the standard JWT claims
    assert jwt_token.issuer == "https://clinical-data-gateway-api.sandbox.nhs.uk"
    assert jwt_token.subject == "10019"
    assert jwt_token.audience == provider_endpoint

    # Verify the requesting organization matches the consumer ODS
    assert jwt_token.requesting_organization["identifier"][0]["value"] == consumer_ods


def test_controller_respects_pds_url(
    mocker: MockerFixture,
    happy_path_pds_response_body: dict[str, Any],
) -> None:
    """
    Test that the controller uses the PDS URL provided in the constructor.
    """
    mocked_get_pds = mocker.patch(
        "gateway_api.pds.client.get",
        return_value=FakeResponse(
            status_code=200, headers={}, _json=happy_path_pds_response_body
        ),
    )
    custom_pds_url = "https://a.different.url/base"

    controller = create_test_controller(pds_base_url=custom_pds_url)
    controller._get_pds_details("auth_token", "9000000009")

    actual_pds_url = mocked_get_pds.call_args.args[0]
    assert actual_pds_url == "https://a.different.url/base/Patient/9000000009"


def test_controller_respects_sds_vars(
    mocker: MockerFixture,
) -> None:
    """
    Test that the controller uses the SDS URL and API token provided in the constructor.
    """
    provider_sds_results = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    consumer_sds_results = SdsSearchResults(
        asid="ConsumerASID", endpoint="https://example.consumer.org/endpoint"
    )
    sds_results = [provider_sds_results, consumer_sds_results]
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=sds_results,
    )
    mocked_sds_client = mocker.patch(
        "gateway_api.controller.SdsClient.__init__", return_value=None
    )
    custom_sds_url = "https://a.different.url/base"
    custom_sds_api_token = "custom-sds-api-token"  # noqa: S105 Not a real token

    controller = create_test_controller(
        sds_base_url=custom_sds_url, sds_api_key=custom_sds_api_token
    )
    controller._get_sds_details("test-ods-1", "test-ods-2")

    actual_sds_url = mocked_sds_client.call_args.kwargs["base_url"]
    actual_sds_api_token = mocked_sds_client.call_args.kwargs["api_key"]
    assert actual_sds_url == "https://a.different.url/base"
    assert actual_sds_api_token == custom_sds_api_token
