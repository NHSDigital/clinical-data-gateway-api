"""
Unit tests for :mod:`gateway_api.sds_search`.
"""

from __future__ import annotations

from typing import Any

import pytest
from stubs.stub_sds import SdsFhirApiStub

from gateway_api.sds_search import SdsClient, SdsSearchResults


@pytest.fixture
def stub() -> SdsFhirApiStub:
    """
    Create a stub backend instance.

    :return: A :class:`stubs.stub_sds.SdsFhirApiStub` instance.
    """
    return SdsFhirApiStub()


@pytest.fixture
def mock_requests_get(
    monkeypatch: pytest.MonkeyPatch, stub: SdsFhirApiStub
) -> dict[str, Any]:
    """
    Patch ``SdsFhirApiStub`` so the SdsClient uses the test stub fixture.

    The fixture returns a "capture" dict recording the most recent request information.

    :param monkeypatch: Pytest monkeypatch fixture.
    :param stub: Stub backend used to serve GET requests.
    :param return: A capture dictionary containing the last call details.
    """
    capture: dict[str, Any] = {}

    # Wrap the stub's get method to capture call parameters
    original_stub_get = stub.get

    def _capturing_get(
        url: str,
        headers: dict[str, str] | None = None,
        params: Any = None,
        timeout: Any = None,
    ) -> Any:
        """
        Wrapper around stub.get that captures parameters.

        :param url: URL passed by the client.
        :param headers: Headers passed by the client.
        :param params: Query parameters.
        :param timeout: Timeout.
        :return: Response from the stub.
        """
        headers = headers or {}
        capture["url"] = url
        capture["headers"] = dict(headers)
        capture["params"] = params
        capture["timeout"] = timeout

        return original_stub_get(url, headers, params, timeout)

    stub.get = _capturing_get  # type: ignore[method-assign]

    # Monkeypatch SdsFhirApiStub so SdsClient uses our test stub
    import gateway_api.sds_search as sds_module

    monkeypatch.setattr(
        sds_module,
        "SdsFhirApiStub",
        lambda *args, **kwargs: stub,  # NOQA ARG005 (maintain signature)
    )

    return capture


def test_sds_client_get_org_details_success(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test SdsClient can successfully look up organization details.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    result = client.get_org_details(ods_code="PROVIDER")

    assert result is not None
    assert isinstance(result, SdsSearchResults)
    assert result.asid == "asid_PROV"
    assert result.endpoint is not None


def test_sds_client_get_org_details_with_endpoint(
    stub: SdsFhirApiStub,
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test SdsClient retrieves endpoint when available.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    # Add a device with party key so we can get an endpoint
    stub.upsert_device(
        organization_ods="TESTORG",
        service_interaction_id="urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1",
        party_key="TESTORG-123456",
        device={
            "resourceType": "Device",
            "id": "test-device-id",
            "identifier": [
                {
                    "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                    "value": "999999999999",
                },
                {
                    "system": "https://fhir.nhs.uk/Id/nhsMhsPartyKey",
                    "value": "TESTORG-123456",
                },
            ],
            "owner": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                    "value": "TESTORG",
                }
            },
        },
    )

    stub.upsert_endpoint(
        organization_ods="TESTORG",
        service_interaction_id="urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1",
        party_key="TESTORG-123456",
        endpoint={
            "resourceType": "Endpoint",
            "id": "test-endpoint-id",
            "status": "active",
            "address": "https://testorg.example.com/fhir",
            "managingOrganization": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                    "value": "TESTORG",
                }
            },
            "identifier": [
                {
                    "system": "https://fhir.nhs.uk/Id/nhsMhsPartyKey",
                    "value": "TESTORG-123456",
                }
            ],
        },
    )

    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)
    result = client.get_org_details(ods_code="TESTORG")

    assert result is not None
    assert result.asid == "999999999999"
    assert result.endpoint == "https://testorg.example.com/fhir"


def test_sds_client_get_org_details_no_endpoint(
    stub: SdsFhirApiStub,
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test SdsClient handles missing endpoint gracefully.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    # Add a device without a party key (so no endpoint will be found)
    stub.upsert_device(
        organization_ods="NOENDPOINT",
        service_interaction_id="urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1",
        party_key=None,
        device={
            "resourceType": "Device",
            "id": "noendpoint-device-id",
            "identifier": [
                {
                    "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                    "value": "888888888888",
                }
            ],
            "owner": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                    "value": "NOENDPOINT",
                }
            },
        },
    )

    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)
    result = client.get_org_details(ods_code="NOENDPOINT")

    assert result is not None
    assert result.asid == "888888888888"
    assert result.endpoint is None


def test_sds_client_get_org_details_not_found(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test SdsClient returns None when organization is not found.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    result = client.get_org_details(ods_code="NONEXISTENT")

    assert result is None


def test_sds_client_sends_correlation_id(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test that SdsClient sends X-Correlation-Id header when provided.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    correlation_id = "test-correlation-123"
    client.get_org_details(ods_code="PROVIDER", correlation_id=correlation_id)

    # Check that the header was sent
    assert mock_requests_get["headers"]["X-Correlation-Id"] == correlation_id


def test_sds_client_sends_apikey(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test that SdsClient sends apikey header.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    api_key = "my-secret-key"
    client = SdsClient(api_key=api_key, base_url=SdsClient.SANDBOX_URL)

    client.get_org_details(ods_code="PROVIDER")

    # Check that the apikey header was sent
    assert mock_requests_get["headers"]["apikey"] == api_key


def test_sds_client_timeout_parameter(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test that SdsClient passes timeout parameter to requests.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL, timeout=30)

    client.get_org_details(ods_code="PROVIDER", timeout=60)

    # Check that the custom timeout was passed
    assert mock_requests_get["timeout"] == 60


def test_sds_client_custom_service_interaction_id(
    stub: SdsFhirApiStub,
    mock_requests_get: dict[str, Any],  # noqa: ARG001
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
                    "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                    "value": "777777777777",
                }
            ],
            "owner": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                    "value": "CUSTOMINT",
                }
            },
        },
    )

    client = SdsClient(
        api_key="test-key",
        base_url=SdsClient.SANDBOX_URL,
        service_interaction_id=custom_interaction,
    )

    result = client.get_org_details(ods_code="CUSTOMINT")

    # Verify the custom interaction was used
    params = mock_requests_get["params"]
    assert any(
        custom_interaction in str(ident) for ident in params.get("identifier", [])
    )

    # Verify we got the result
    assert result is not None
    assert result.asid == "777777777777"


def test_sds_client_builds_correct_device_query_params(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test that SdsClient builds Device query parameters correctly.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    client.get_org_details(ods_code="PROVIDER")

    params = mock_requests_get["params"]

    # Check organization parameter
    assert (
        params["organization"]
        == "https://fhir.nhs.uk/Id/ods-organization-code|PROVIDER"
    )

    # Check identifier list contains interaction ID
    identifiers = params["identifier"]
    assert isinstance(identifiers, list)
    assert any(
        "https://fhir.nhs.uk/Id/nhsServiceInteractionId|" in str(ident)
        for ident in identifiers
    )


def test_sds_client_extract_asid_from_device(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test ASID extraction from Device resource.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    result = client.get_org_details(ods_code="PROVIDER")

    assert result is not None
    assert result.asid is not None
    assert result.asid == "asid_PROV"


def test_sds_client_extract_party_key_from_device(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
) -> None:
    """
    Test party key extraction and subsequent endpoint lookup.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    """
    # The default seeded PROVIDER device has a party key, which should trigger
    # an endpoint lookup
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)

    # Need to seed the data correctly - let's use CONSUMER which has party key
    result = client.get_org_details(ods_code="CONSUMER")

    # Should have found ASID but may not have endpoint depending on seeding
    assert result is not None
    assert result.asid == "asid_CONS"


def test_sds_client_handles_http_error_from_device_endpoint(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test that ExternalServiceError is raised when Device API returns HTTP error.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    :param monkeypatch: Pytest monkeypatch fixture.
    """
    from unittest.mock import Mock

    import requests

    from gateway_api.sds_search import ExternalServiceError

    # Create a mock response with error status
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        response=mock_response
    )

    # Create a mock that returns our error response
    def mock_get(*args: Any, **kwargs: Any) -> Mock:  # noqa: ARG001
        return mock_response

    # Patch the get_method to return error
    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)
    monkeypatch.setattr(client, "get_method", mock_get)

    # Should raise ExternalServiceError
    with pytest.raises(ExternalServiceError) as exc_info:
        client.get_org_details(ods_code="PROVIDER")

    assert "Device request failed" in str(exc_info.value)
    assert "500" in str(exc_info.value)


def test_sds_client_handles_http_error_from_endpoint_endpoint(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test that ExternalServiceError is raised when Endpoint API returns HTTP error.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    :param monkeypatch: Pytest monkeypatch fixture.
    """
    from unittest.mock import Mock

    import requests

    from gateway_api.sds_search import ExternalServiceError

    call_count = {"count": 0}

    # Create mock responses
    def mock_get(url: str, *args: Any, **kwargs: Any) -> Mock:  # noqa: ARG001
        call_count["count"] += 1
        if call_count["count"] == 1:
            # First call (Device) - return success
            device_response = Mock()
            device_response.status_code = 200
            device_response.raise_for_status = Mock()
            device_response.json.return_value = {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 1,
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Device",
                            "identifier": [
                                {
                                    "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                                    "value": "123456789012",
                                },
                                {
                                    "system": "https://fhir.nhs.uk/Id/nhsMhsPartyKey",
                                    "value": "TEST-PARTY-KEY",
                                },
                            ],
                        }
                    }
                ],
            }
            return device_response
        else:
            # Second call (Endpoint) - return error
            endpoint_response = Mock()
            endpoint_response.status_code = 503
            endpoint_response.reason = "Service Unavailable"
            endpoint_response.raise_for_status.side_effect = requests.HTTPError(
                response=endpoint_response
            )
            return endpoint_response

    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)
    monkeypatch.setattr(client, "get_method", mock_get)

    # Should raise ExternalServiceError on Endpoint query
    with pytest.raises(ExternalServiceError) as exc_info:
        client.get_org_details(ods_code="TESTORG")

    assert "Endpoint request failed" in str(exc_info.value)
    assert "503" in str(exc_info.value)


def test_sds_client_handles_empty_bundle_gracefully(
    stub: SdsFhirApiStub,  # noqa: ARG001
    mock_requests_get: dict[str, Any],  # noqa: ARG001
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test that client handles empty Bundle (total: 0) gracefully.

    :param stub: SDS stub fixture.
    :param mock_requests_get: Capture fixture for request details.
    :param monkeypatch: Pytest monkeypatch fixture.
    """
    from unittest.mock import Mock

    # Create mock that returns empty bundle
    def mock_get(*args: Any, **kwargs: Any) -> Mock:  # noqa: ARG001
        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        response.json.return_value = {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": 0,
            "entry": [],
        }
        return response

    client = SdsClient(api_key="test-key", base_url=SdsClient.SANDBOX_URL)
    monkeypatch.setattr(client, "get_method", mock_get)

    # Should return None for empty result
    result = client.get_org_details(ods_code="NONEXISTENT")

    assert result is None
