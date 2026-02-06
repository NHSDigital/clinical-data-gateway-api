"""
SDS (Spine Directory Service) FHIR R4 device and endpoint lookup client.

This module provides a client for querying the Spine Directory Service to retrieve:
- Device records (including ASID - Accredited System ID)
- Endpoint records (including endpoint URLs for routing)

The client is structured similarly to :mod:`gateway_api.pds_search` and supports
stubbing for testing purposes.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

import requests
from stubs.stub_sds import SdsFhirApiStub

# Recursive JSON-like structure typing used for parsed FHIR bodies.
type ResultStructure = str | dict[str, "ResultStructure"] | list["ResultStructure"]
type ResultStructureDict = dict[str, ResultStructure]
type ResultList = list[ResultStructureDict]

# Type for stub get method
type GetCallable = Callable[..., requests.Response]


class ExternalServiceError(Exception):
    """
    Raised when the downstream SDS request fails.

    This module catches :class:`requests.HTTPError` thrown by
    ``response.raise_for_status()`` and re-raises it as ``ExternalServiceError`` so
    callers are not coupled to ``requests`` exception types.
    """


@dataclass
class SdsSearchResults:
    """
    SDS lookup results containing ASID and endpoint information.

    :param asid: Accredited System ID extracted from the Device resource.
    :param endpoint: Endpoint URL extracted from the Endpoint resource, or ``None``
        if no endpoint is available.
    """

    asid: str | None
    endpoint: str | None


class SdsClient:
    """
    Simple client for SDS FHIR R4 device and endpoint retrieval.

    The client supports:

    * :meth:`get_org_details` - Retrieves ASID and endpoint for an organization

    This method returns a :class:`SdsSearchResults` instance when data can be
    extracted, otherwise ``None``.

    **Usage example**::

        sds = SdsClient(
            api_key="YOUR_API_KEY",
            base_url="https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4",
        )

        result = sds.get_org_details("A12345")

        if result:
            print(f"ASID: {result.asid}, Endpoint: {result.endpoint}")
    """

    # URLs for different SDS environments
    SANDBOX_URL = "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
    INT_URL = "https://int.api.service.nhs.uk/spine-directory/FHIR/R4"
    DEP_UAT_URL = "https://dep.api.service.nhs.uk/spine-directory/FHIR/R4"
    PROD_URL = "https://api.service.nhs.uk/spine-directory/FHIR/R4"

    # FHIR identifier systems
    ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
    INTERACTION_SYSTEM = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
    PARTYKEY_SYSTEM = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
    ASID_SYSTEM = "https://fhir.nhs.uk/Id/nhsSpineASID"

    # SDS resource types
    DEVICE: Literal["Device"] = "Device"
    ENDPOINT: Literal["Endpoint"] = "Endpoint"

    # Default service interaction ID for GP Connect
    DEFAULT_SERVICE_INTERACTION_ID = (
        "urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1"
    )

    def __init__(
        self,
        api_key: str,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
        service_interaction_id: str | None = None,
    ) -> None:
        """
        Create an SDS client.

        :param api_key: API key for SDS authentication (header 'apikey').
        :param base_url: Base URL for the SDS API. Trailing slashes are stripped.
        :param timeout: Default timeout in seconds for HTTP calls.
        :param service_interaction_id: Service interaction ID to use for lookups.
            If not provided, uses :attr:`DEFAULT_SERVICE_INTERACTION_ID`.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.service_interaction_id = (
            service_interaction_id or self.DEFAULT_SERVICE_INTERACTION_ID
        )
        self.stub = SdsFhirApiStub()

        # Use stub for now - use environment variable once we have one
        # TODO: Put this back to using the environment variable
        # if os.environ.get("STUB_SDS", None):
        self.get_method: GetCallable = self.stub.get
        # else:
        #     self.get_method: GetCallable = requests.get

    def _build_headers(self, correlation_id: str | None = None) -> dict[str, str]:
        """
        Build mandatory and optional headers for an SDS request.

        :param correlation_id: Optional ``X-Correlation-Id`` for cross-system tracing.
        :return: Dictionary of HTTP headers for the outbound request.
        """
        headers = {
            "Accept": "application/fhir+json",
            "apikey": self.api_key,
        }

        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id

        return headers

    def get_org_details(
        self,
        ods_code: str,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> SdsSearchResults | None:
        """
        Retrieve ASID and endpoint for an organization by ODS code.

        This method performs two SDS queries:
        1. Query /Device to get the ASID for the organization
        2. Query /Endpoint to get the endpoint URL (if available)

        :param ods_code: ODS code of the organization to look up.
        :param correlation_id: Optional correlation ID for tracing.
        :param timeout: Optional per-call timeout in seconds. If not provided,
            :attr:`timeout` is used.
        :return: A :class:`SdsSearchResults` instance if data can be extracted,
            otherwise ``None``.
        :raises ExternalServiceError: If the HTTP request returns an error status.
        """
        # Step 1: Get Device to obtain ASID
        device_bundle = self._query_sds(
            ods_code=ods_code,
            correlation_id=correlation_id,
            timeout=timeout,
            querytype=self.DEVICE,
        )

        device = self._extract_first_entry(device_bundle)
        if device is None:
            return None

        asid = self._extract_identifier(device, self.ASID_SYSTEM)
        party_key = self._extract_identifier(device, self.PARTYKEY_SYSTEM)

        # Step 2: Get Endpoint to obtain endpoint URL
        endpoint_url: str | None = None
        if party_key:
            endpoint_bundle = self._query_sds(
                ods_code=ods_code,
                party_key=party_key,
                correlation_id=correlation_id,
                timeout=timeout,
                querytype=self.ENDPOINT,
            )
            endpoint = self._extract_first_entry(endpoint_bundle)
            if endpoint:
                address = endpoint.get("address")
                if address:
                    endpoint_url = str(address).strip()

        return SdsSearchResults(asid=asid, endpoint=endpoint_url)

    def _query_sds(
        self,
        ods_code: str,
        party_key: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = 10,
        querytype: Literal["Device", "Endpoint"] = DEVICE,
    ) -> ResultStructureDict:
        """
        Query SDS /Device or /Endpoint endpoint.

        :param ods_code: ODS code to search for.
        :param party_key: Party key to search for.
        :param correlation_id: Optional correlation ID.
        :param timeout: Optional timeout.
        :return: Parsed JSON response as a dictionary.
        :raises ExternalServiceError: If the request fails.
        """
        headers = self._build_headers(correlation_id=correlation_id)
        url = f"{self.base_url}/{querytype}"

        params: dict[str, Any] = {
            "organization": f"{self.ODS_SYSTEM}|{ods_code}",
            "identifier": [f"{self.INTERACTION_SYSTEM}|{self.service_interaction_id}"],
        }

        if party_key is not None:
            params["identifier"].append(f"{self.PARTYKEY_SYSTEM}|{party_key}")

        response = self.get_method(
            url,
            headers=headers,
            params=params,
            timeout=timeout or self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise ExternalServiceError(
                f"SDS /{querytype} request failed: {err.response.status_code} "
                f"{err.response.reason}"
            ) from err

        body = response.json()
        return cast("ResultStructureDict", body)

    # --------------- internal helpers for result extraction -----------------

    @staticmethod
    def _extract_first_entry(
        bundle: ResultStructureDict,
    ) -> ResultStructureDict | None:
        """
        Extract the first Device resource from a Bundle.

        :param bundle: FHIR Bundle containing Device resources.
        :return: First Device resource, or ``None`` if the bundle is empty.
        """
        entries = cast("ResultList", bundle.get("entry", []))
        if not entries:
            return None

        first_entry = entries[0]
        return cast("ResultStructureDict", first_entry.get("resource", {}))

    def _extract_identifier(
        self, device: ResultStructureDict, system: str
    ) -> str | None:
        """
        Extract an identifier value from a Device resource for a given system.

        :param device: Device resource dictionary.
        :param system: The identifier system to look for.
        :return: Identifier value if found, otherwise ``None``.
        """
        identifiers = cast("ResultList", device.get("identifier", []))

        for identifier in identifiers:
            id_system = str(identifier.get("system", ""))
            if id_system == system:
                value = identifier.get("value")
                if value:
                    return str(value).strip()

        return None
