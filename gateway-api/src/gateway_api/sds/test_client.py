"""
Unit tests for :mod:`gateway_api.sds_search`.
"""

from __future__ import annotations

import pytest
from fhir.constants import FHIRSystem
from stubs.sds.stub import SdsFhirApiStub

from gateway_api.common.error import SdsRequestFailedError
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
    client = SdsClient(base_url=SdsClient.INT_URL)

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
        device={
            "resourceType": "Device",
            "id": "test-device-id",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "999999999999",
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
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "999999999999",
                },
            ],
        },
    )

    client = SdsClient(base_url=SdsClient.INT_URL)
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
    client = SdsClient(base_url=SdsClient.INT_URL)

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
    client = SdsClient(base_url=SdsClient.INT_URL, timeout=30)

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
        base_url=SdsClient.INT_URL,
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
    client = SdsClient(base_url=SdsClient.INT_URL)

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


def test_sds_client_uses_sandbox_interaction_id_for_sandbox_url(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that SdsClient uses SANDBOX_INTERACTION_ID when connecting to the
    sandbox environment, not the default ACCESS_RECORD_STRUCTURED_INTERACTION_ID.

    :param stub: SDS stub fixture.
    """
    sandbox_interaction_id = SdsClient.SANDBOX_INTERACTION_ID

    # Seed the stub with data keyed by the sandbox interaction ID
    stub.upsert_device(
        organization_ods="SANDBOXORG",
        service_interaction_id=sandbox_interaction_id,
        device={
            "resourceType": "Device",
            "id": "sandbox-device-id",
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": "555555555555",
                },
            ],
            "owner": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": "SANDBOXORG",
                }
            },
        },
    )

    client = SdsClient(base_url=SdsClient.SANDBOX_URL)
    result = client.get_org_details(ods_code="SANDBOXORG", get_endpoint=False)

    # Verify the sandbox interaction ID was sent
    params = stub.get_params
    assert any(
        sandbox_interaction_id in str(ident) for ident in params.get("identifier", [])
    )
    # Verify the default interaction ID was NOT used
    assert not any(
        ACCESS_RECORD_STRUCTURED_INTERACTION_ID in str(ident)
        for ident in params.get("identifier", [])
    )

    assert result is not None
    assert result.asid == "555555555555"


def test_sds_client_raises_sds_request_failed_error_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test that SdsClient raises SdsRequestFailedError when SDS returns
    a non-2xx response.

    :param monkeypatch: Pytest monkeypatch fixture.
    """
    stub = SdsFhirApiStub()

    def get_without_apikey(
        url: str,
        headers: dict[str, str],
        params: dict[str, str],
        timeout: int = 10,
    ) -> object:
        # Strip the apikey header so the stub returns a 400
        headers_without_key = {k: v for k, v in headers.items() if k != "apikey"}
        return stub.get(
            url=url, headers=headers_without_key, params=params, timeout=timeout
        )

    monkeypatch.setattr("gateway_api.sds.client.get", get_without_apikey)

    client = SdsClient(base_url=SdsClient.SANDBOX_URL)

    with pytest.raises(SdsRequestFailedError, match="SDS FHIR API request failed"):
        client.get_org_details(ods_code="PROVIDER")


def test_sds_client_endpoint_entry_without_address_returns_none(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that get_org_details returns endpoint=None when the Endpoint resource
    has no address field.

    :param stub: SDS stub fixture.
    """
    stub.upsert_device(
        organization_ods="NOADDR",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        device={
            "resourceType": "Device",
            "id": "noaddr-device",
            "identifier": [
                {"system": FHIRSystem.NHS_SPINE_ASID, "value": "111111111111"},
            ],
        },
    )
    stub.upsert_endpoint(
        organization_ods="NOADDR",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        endpoint={
            "resourceType": "Endpoint",
            "id": "noaddr-endpoint",
            "status": "active",
            # no "address" field
            "identifier": [
                {"system": FHIRSystem.NHS_SPINE_ASID, "value": "111111111111"}
            ],
        },
    )

    client = SdsClient(base_url=SdsClient.INT_URL)
    result = client.get_org_details(ods_code="NOADDR")

    assert result.asid == "111111111111"
    assert result.endpoint is None


@pytest.mark.usefixtures("stub")
def test_sds_client_empty_device_bundle_returns_none_asid() -> None:
    """
    Test that get_org_details returns asid=None when the Device bundle has no
    entries for the given ODS code, exercising the empty-entries branch in
    _extract_first_entry.

    :param stub: SDS stub fixture.
    """
    client = SdsClient(base_url=SdsClient.INT_URL)
    # "UNKNOWNORG" has no seeded devices, so the bundle entry list will be empty
    result = client.get_org_details(ods_code="UNKNOWNORG", get_endpoint=False)

    assert result.asid is None


def test_sds_client_no_endpoint_bundle_entries_returns_none_endpoint(
    stub: SdsFhirApiStub,
) -> None:
    """
    Test that get_org_details returns endpoint=None when the Endpoint bundle has
    no entries, exercising the else branch after _extract_first_entry returns {}.

    :param stub: SDS stub fixture.
    """
    stub.upsert_device(
        organization_ods="NOENDPOINT",
        service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
        device={
            "resourceType": "Device",
            "id": "noendpoint-device",
            "identifier": [
                {"system": FHIRSystem.NHS_SPINE_ASID, "value": "222222222222"},
            ],
        },
    )
    # Deliberately do not seed any endpoint for NOENDPOINT

    client = SdsClient(base_url=SdsClient.INT_URL)
    result = client.get_org_details(ods_code="NOENDPOINT")

    assert result.asid == "222222222222"
    assert result.endpoint is None
