"""
Unit tests for :mod:`gateway_api.sds_search`.
"""

from __future__ import annotations

import pytest
from fhir.constants import FHIRSystem
from stubs.sds.stub import SdsFhirApiStub

from gateway_api.get_structured_record import ACCESS_RECORD_STRUCTURED_INTERACTION_ID
from gateway_api.sds import (
    SdsClient,
    SdsSearchResults,
)


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> SdsFhirApiStub:
    stub = SdsFhirApiStub()
    monkeypatch.setattr(
        "gateway_api.sds.client.get",
        lambda *args, **kwargs: stub.get(*args, **kwargs),  # NOQA ARG005 (maintain signature)
    )
    monkeypatch.setattr("requests.get", stub.get)

    return stub


def test_sds_client_get_org_details_success(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test SdsClient can successfully look up organization details.

    :param stub: SDS stub fixture.
    """
    client = SdsClient(base_url=SdsClient.SANDBOX_URL)

    result = client.get_org_details(ods_code="PROVIDER")

    assert result is not None
    assert isinstance(result, SdsSearchResults)
    assert result.asid == "asid_PROV"
    assert result.endpoint == "https://provider.example.com/fhir"

    params = stub.get_params
    assert any(
        ACCESS_RECORD_STRUCTURED_INTERACTION_ID in str(ident)
        for ident in params.get("identifier", [])
    )


def test_sds_client_get_org_details_with_endpoint(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test SdsClient retrieves endpoint when available.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """

    # Add a device so we can get an endpoint
    stub.upsert_device(
        organization_ods="TESTORG",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        party_key="TESTORG-123456",
        device={
            "resourceType": "Device",
            "id": "test-device-id",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "999999999999",
                },
                {
                    "system": FHIRSystem.NHS_MHS_PARTY_KEY,
                    "value": "TESTORG-123456",
                },
            ],
            "owner": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": "TESTORG",
                }
            },
        },
    )

    stub.upsert_endpoint(
        organization_ods="TESTORG",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        party_key="TESTORG-123456",
        endpoint={
            "resourceType": "Endpoint",
            "id": "test-endpoint-id",
            "status": "active",
            "address": "https://testorg.example.com/fhir",
            "managingOrganization": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": "TESTORG",
                }
            },
            "identifier": [
                {
                    "system": FHIRSystem.NHS_MHS_PARTY_KEY,
                    "value": "TESTORG-123456",
                }
            ],
        },
    )

    client = SdsClient(base_url=SdsClient.SANDBOX_URL)
    result = client.get_org_details(ods_code="TESTORG")

    assert result is not None
    assert result.asid == "999999999999"
    assert result.endpoint == "https://testorg.example.com/fhir"


def test_sds_client_sends_correct_headers(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that SdsClient sends X-Correlation-Id and apikey headers when provided.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(base_url=SdsClient.SANDBOX_URL)

    correlation_id = "test-correlation-123"
    client.get_org_details(ods_code="PROVIDER", correlation_id=correlation_id)

    # Check that the headers were
    assert stub.get_headers["X-Correlation-Id"] == correlation_id

    # In future when _get_api_key calls AWS secrets, this will break.
    # That's a good thing, because we'll want to mock that call.
    assert stub.get_headers["apikey"] == "test_api_key_DO_NOT_REPLACE_HERE"


def test_sds_client_timeout_parameter(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that SdsClient passes timeout parameter to requests.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(base_url=SdsClient.SANDBOX_URL, timeout=30)

    client.get_org_details(ods_code="PROVIDER", timeout=60)

    # Check that the custom timeout was passed
    assert stub.get_timeout == 60


def test_sds_client_custom_service_interaction_id(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that SdsClient uses custom interaction ID when provided.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    custom_interaction = "urn:nhs:names:services:custom:CUSTOM123"

    # Add device with custom interaction ID
    stub.upsert_device(
        organization_ods="CUSTOMINT",
        service_interaction_id=custom_interaction,
        party_key=None,
        device={
            "resourceType": "Device",
            "id": "custom-device",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "777777777777",
                }
            ],
            "owner": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": "CUSTOMINT",
                }
            },
        },
    )

    client = SdsClient(
        base_url=SdsClient.SANDBOX_URL,
        service_interaction_id=custom_interaction,
    )

    result = client.get_org_details(ods_code="CUSTOMINT", get_endpoint=False)

    # Verify the custom interaction was used
    params = stub.get_params
    assert any(
        custom_interaction in str(ident) for ident in params.get("identifier", [])
    )

    # Verify we got the result
    assert result is not None
    assert result.asid == "777777777777"


def test_sds_client_builds_correct_device_query_params(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that SdsClient builds Device query parameters correctly.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(base_url=SdsClient.SANDBOX_URL)

    client.get_org_details(ods_code="PROVIDER")

    params = stub.get_params

    # Check organization parameter
    assert params["organization"] == f"{FHIRSystem.ODS_CODE}|PROVIDER"

    # Check identifier list contains interaction ID
    identifiers = params["identifier"]
    assert isinstance(identifiers, list)
    assert any(
        f"{FHIRSystem.NHS_SERVICE_INTERACTION_ID}|" in str(ident)
        for ident in identifiers
    )


def test_sds_client_extract_party_key_from_device(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test party key extraction and subsequent endpoint lookup.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    # The default seeded PROVIDER device has a party key
    client = SdsClient(base_url=SdsClient.SANDBOX_URL)

    stub.upsert_device(
        organization_ods="WITHPARTYKEY",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        party_key="WITHPARTYKEY-654321",
        device={
            "resourceType": "Device",
            "id": "device-with-party-key",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "888888888888",
                },
                {
                    "system": FHIRSystem.NHS_MHS_PARTY_KEY,
                    "value": "WITHPARTYKEY-654321",
                },
            ],
        },
    )

    stub.upsert_endpoint(
        organization_ods="WITHPARTYKEY",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        party_key="WITHPARTYKEY-654321",
        endpoint={
            "resourceType": "Endpoint",
            "id": "endpoint-for-party-key",
            "status": "active",
            "address": "https://withpartykey.example.com/fhir",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_MHS_PARTY_KEY,
                    "value": "WITHPARTYKEY-654321",
                }
            ],
        },
    )

    result = client.get_org_details(ods_code="WITHPARTYKEY", get_endpoint=True)

    # Should have found ASID but may not have endpoint depending on seeding
    assert result is not None
    assert result.asid == "888888888888"
    assert result.endpoint == "https://withpartykey.example.com/fhir"
