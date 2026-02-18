"""Integration tests for SDS (Spine Directory Service) search functionality."""

from __future__ import annotations

from gateway_api.sds_search import SdsClient, SdsSearchResults


class TestSdsIntegration:
    """Integration tests for SDS search operations."""

    def test_get_device_by_ods_code_returns_valid_asid(self) -> None:
        """
        Test that querying by ODS code returns a valid ASID.

        :param sds_client: SDS client fixture configured with stub.
        """
        sds_client = SdsClient()
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        assert isinstance(result, SdsSearchResults)
        assert result.asid is not None
        assert result.asid == "asid_PROV"
        assert len(result.asid) > 0

    def test_get_device_with_party_key_returns_endpoint(self) -> None:
        """
        Test that a device with party key returns both ASID and endpoint.

        :param sds_client: SDS client fixture configured with stub.
        """
        sds_client = SdsClient()
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        assert result.asid == "asid_PROV"
        assert result.endpoint is not None
        assert result.endpoint == "https://provider.example.com/fhir"
        # Verify endpoint is a valid URL format
        assert result.endpoint.startswith("https://")
        assert "fhir" in result.endpoint

    def test_consumer_organization_lookup(self) -> None:
        """
        Test that CONSUMER organization can be looked up successfully.

        :param sds_client: SDS client fixture configured with stub.
        """
        sds_client = SdsClient()
        result = sds_client.get_org_details(ods_code="CONSUMER")

        assert result is not None
        assert result.asid == "asid_CONS"
        assert result.endpoint is not None
        assert result.endpoint == "https://consumer.example.com/fhir"

    def test_result_contains_both_asid_and_endpoint_when_available(self) -> None:
        """
        Test that results contain both ASID and endpoint when both are available.

        :param sds_client: SDS client fixture configured with stub.
        """

        sds_client = SdsClient()
        result = sds_client.get_org_details(ods_code="PROVIDER")

        assert result is not None
        # Verify both fields are present and not None
        assert hasattr(result, "asid")
        assert hasattr(result, "endpoint")
        assert result.asid is not None
        assert result.endpoint is not None
