from gateway_api.sds.client import SdsClient


def test_sds_client(auth_token: str) -> None:
    """Test that the SDS client returns the expected ASID and endpoint."""
    sds_client = SdsClient(
        auth_token=auth_token, base_url="https://example.invalid/sds"
    )
    result = sds_client.get_org_details("test_ods_code")
    assert result is not None
    assert result.asid == "asid_test_ods_code"
