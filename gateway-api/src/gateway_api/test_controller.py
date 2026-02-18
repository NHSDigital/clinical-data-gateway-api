"""Unit tests for :mod:`gateway_api.controller`."""

import pytest
from pytest_mock import MockerFixture

from gateway_api.common.error import (
    NoAsidFound,
    NoCurrentEndpoint,
    NoCurrentProvider,
    NoOrganisationFound,
)
from gateway_api.controller import Controller
from gateway_api.pds import PdsSearchResults
from gateway_api.sds import SdsSearchResults


def test_get_pds_details_returns_provider_ods_code_for_happy_path(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    nhs_number = "9000000009"
    pds_search_result = PdsSearchResults(
        given_names="Jane",
        family_name="Smith",
        nhs_number=nhs_number,
        gp_ods_code="A12345",
    )
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=pds_search_result,
    )
    controller = Controller(pds_base_url="https://example.test/pds", timeout=7)

    actual = controller._get_pds_details(auth_token, nhs_number)  # noqa: SLF001

    assert actual == "A12345"


def test_get_pds_details_raises_no_current_provider_when_ods_code_missing_in_pds(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    nhs_number = "9000000009"
    pds_search_result_without_ods_code = PdsSearchResults(
        given_names="Jane",
        family_name="Smith",
        nhs_number=nhs_number,
        gp_ods_code=None,
    )
    mocker.patch(
        "gateway_api.pds.PdsClient.search_patient_by_nhs_number",
        return_value=pds_search_result_without_ods_code,
    )

    controller = Controller()

    with pytest.raises(
        NoCurrentProvider,
        match="PDS patient 9000000009 did not contain a current provider ODS code",
    ):
        _ = controller._get_pds_details(auth_token, nhs_number)  # noqa: SLF001


def test_get_sds_details_returns_consumer_and_provider_deatils_for_happy_path(
    mocker: MockerFixture,
    auth_token: str,
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

    controller = Controller()

    expected = ("ConsumerASID", "ProviderASID", "https://example.provider.org/endpoint")
    actual = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001
    assert actual == expected


def test_get_sds_details_raises_no_organisation_found_when_sds_returns_none(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        return_value=None,
    )

    controller = Controller()

    with pytest.raises(
        NoOrganisationFound,
        match="No SDS org found for provider ODS code ProviderODS",
    ):
        _ = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001


def test_get_sds_details_raises_no_asid_found_when_sds_returns_empty_asid(
    mocker: MockerFixture,
    auth_token: str,
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

    controller = Controller()

    with pytest.raises(
        NoAsidFound,
        match=(
            "SDS result for provider ODS code ProviderODS did not contain "
            "a current ASID"
        ),
    ):
        _ = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001


def test_get_sds_details_raises_no_current_endpoint_when_sds_returns_empty_endpoint(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"
    blank_endpoint_sds_result = SdsSearchResults(asid="ProviderASID", endpoint="   ")
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        return_value=blank_endpoint_sds_result,
    )

    controller = Controller()

    with pytest.raises(
        NoCurrentEndpoint,
        match=(
            "SDS result for provider ODS code ProviderODS did "
            "not contain a current endpoint"
        ),
    ):
        _ = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001


def test_get_sds_details_raises_no_org_found_when_sds_returns_none_for_consumer(
    mocker: MockerFixture,
    auth_token: str,
) -> None:
    provider_ods = "ProviderODS"
    consumer_ods = "ConsumerODS"

    happy_path_provider_sds_result = SdsSearchResults(
        asid="ProviderASID", endpoint="https://example.provider.org/endpoint"
    )
    none_result_for_consumer = None
    mocker.patch(
        "gateway_api.sds.SdsClient.get_org_details",
        side_effect=[happy_path_provider_sds_result, none_result_for_consumer],
    )

    controller = Controller()

    with pytest.raises(
        NoOrganisationFound,
        match="No SDS org found for consumer ODS code ConsumerODS",
    ):
        _ = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001


def test_get_sds_details_raises_no_asid_found_when_sds_returns_empty_consumer_asid(
    mocker: MockerFixture,
    auth_token: str,
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

    controller = Controller()

    with pytest.raises(
        NoAsidFound,
        match=(
            "SDS result for consumer ODS code ConsumerODS did not contain "
            "a current ASID"
        ),
    ):
        _ = controller._get_sds_details(auth_token, consumer_ods, provider_ods)  # noqa: SLF001
