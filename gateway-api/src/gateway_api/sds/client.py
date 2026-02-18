from gateway_api.sds.search_results import SdsSearchResults


class SdsClient:
    """
    Stub SDS client for obtaining ASID from ODS code.

    Replace this with the real one once it's implemented.
    """

    SANDBOX_URL = "https://example.invalid/sds"

    def __init__(
        self,
        auth_token: str,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
    ) -> None:
        """
        Create an SDS client.
        """
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        """
        Retrieve SDS org details for a given ODS code.

        This is a placeholder implementation that always returns an ASID and endpoint.
        """
        # Placeholder implementation
        return SdsSearchResults(
            asid=f"asid_{ods_code}", endpoint="https://example-provider.org/endpoint"
        )
