"""Integration tests for SDS (Spine Directory Service) search functionality."""

from __future__ import annotations

import pytest
from gateway_api.sds_search import SdsClient, SdsSearchResults
from stubs.stub_sds import SdsFhirApiStub


@pytest.fixture
def sds_stub() -> SdsFhirApiStub:
    """
    Create and return an SDS stub instance with default seeded data.

    :return: SdsFhirApiStub instance with PROVIDER and CONSUMER organizations.
    """
    return SdsFhirApiStub()


@pytest.fixture
def sds_client(sds_stub: SdsFhirApiStub) -> SdsClient:
    """
    Create an SdsClient configured to use the stub.

    :param sds_stub: SDS stub fixture.
    :return: SdsClient configured with test stub.
    """
    client = SdsClient(api_key="test-integration-key", base_url="http://stub")
    # Override the get_method to use the stub
    client.get_method = sds_stub.get
    return client


class TestSdsIntegration:
    """Integration tests for SDS search operations."""

    def test_get_device_by_ods_code_returns_valid_asid(
        self, sds_client: SdsClient
    ) -> None:
        """
        Test that querying by ODS code returns a valid ASID.

        :param sds_client: SDS client fixture configured with stub.
        """
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        assert isinstance(result, SdsSearchResults)
        assert result.asid is not None
        assert result.asid == "asid_PROV"
        assert len(result.asid) > 0

    def test_get_device_with_party_key_returns_endpoint(
        self, sds_client: SdsClient
    ) -> None:
        """
        Test that a device with party key returns both ASID and endpoint.

        :param sds_client: SDS client fixture configured with stub.
        """
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        assert result.asid == "asid_PROV"
        assert result.endpoint is not None
        assert result.endpoint == "https://provider.example.com/fhir"
        # Verify endpoint is a valid URL format
        assert result.endpoint.startswith("https://")
        assert "fhir" in result.endpoint

    def test_get_device_for_nonexistent_ods_returns_none(
        self, sds_client: SdsClient
    ) -> None:
        """
        Test that querying for a non-existent ODS code returns None.

        :param sds_client: SDS client fixture configured with stub.
        """
        result = sds_client.get_org_details(ods_code="NONEXISTENT")

        assert result is None

    def test_missing_required_parameters_returns_400(
        self, sds_stub: SdsFhirApiStub
    ) -> None:
        """
        Test that missing required parameters returns a 400 error.

        :param sds_stub: SDS stub fixture.
        """
        # Test missing organization parameter
        response = sds_stub.get_device_bundle(
            url="http://test/Device",
            headers={"apikey": "test-key"},
            params={
                "identifier": [
                    "https://fhir.nhs.uk/Id/nhsServiceInteractionId|urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1"
                ]
            },
        )

        assert response.status_code == 400
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert body["issue"][0]["severity"] == "error"
        assert "organization" in body["issue"][0]["diagnostics"].lower()

        # Test missing identifier parameter
        response = sds_stub.get_device_bundle(
            url="http://test/Device",
            headers={"apikey": "test-key"},
            params={
                "organization": "https://fhir.nhs.uk/Id/ods-organization-code|PROVIDER"
            },
        )

        assert response.status_code == 400
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert body["issue"][0]["severity"] == "error"
        assert "identifier" in body["issue"][0]["diagnostics"].lower()

        # Test missing service interaction ID in identifier
        response = sds_stub.get_device_bundle(
            url="http://test/Device",
            headers={"apikey": "test-key"},
            params={
                "organization": "https://fhir.nhs.uk/Id/ods-organization-code|PROVIDER",
                "identifier": ["https://fhir.nhs.uk/Id/nhsMhsPartyKey|TEST-KEY"],
            },
        )

        assert response.status_code == 400
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert body["issue"][0]["severity"] == "error"
        assert "nhsServiceInteractionId" in body["issue"][0]["diagnostics"]

    def test_consumer_organization_lookup(self, sds_client: SdsClient) -> None:
        """
        Test that CONSUMER organization can be looked up successfully.

        :param sds_client: SDS client fixture configured with stub.
        """
        result = sds_client.get_org_details(ods_code="CONSUMER")

        assert result is not None
        assert result.asid == "asid_CONS"
        assert result.endpoint is not None
        assert result.endpoint == "https://consumer.example.com/fhir"

    def test_result_contains_both_asid_and_endpoint_when_available(
        self, sds_client: SdsClient
    ) -> None:
        """
        Test that results contain both ASID and endpoint when both are available.

        :param sds_client: SDS client fixture configured with stub.
        """
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        # Verify both fields are present and not None
        assert hasattr(result, "asid")
        assert hasattr(result, "endpoint")
        assert result.asid is not None
        assert result.endpoint is not None
