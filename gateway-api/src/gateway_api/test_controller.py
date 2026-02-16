"""Unit tests for :mod:`gateway_api.controller`."""

import pytest
from pytest_mock import MockerFixture

from gateway_api.common.error import NoCurrentProvider
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
