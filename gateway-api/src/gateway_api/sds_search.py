"""
SDS (Spine Directory Service) FHIR R4 device and endpoint lookup client.

This module provides a client for querying the Spine Directory Service to retrieve:
- Device records (including ASID - Accredited System ID)
- Endpoint records (including endpoint URLs for routing)
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

import requests
from stubs.stub_sds import SdsFhirApiStub

from gateway_api.common.common import ACCESS_RECORD_STRUCTURED_INTERACTION_ID

# Recursive JSON-like structure typing used for parsed FHIR bodies.
type ResultStructure = str | dict[str, "ResultStructure"] | list["ResultStructure"]
type ResultStructureDict = dict[str, ResultStructure]
type ResultList = list[ResultStructureDict]

# Type for stub get method
type GetCallable = Callable[..., requests.Response]


class ExternalServiceError(Exception):
    """
    Raised when the downstream SDS request fails.
    """


@dataclass
class SdsSearchResults:
    """
    SDS lookup results containing ASID and endpoint information.
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

    **Stubbing**:

    For testing, set the environment variable ``$STUB_SDS`` to use the
    :class:`SdsFhirApiStub` instead of making real HTTP requests.

    **Usage example**::

        sds = SdsClient(
            base_url="https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4",
            timeout=10,
            service_interaction_id="urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1",
        )

        result = sds.get_org_details("A12345")

        if result:
            print(f"ASID: {result.asid}, Endpoint: {result.endpoint}")
    """

    # URLs for different SDS environments. Will move to a config file eventually.
    SANDBOX_URL = "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
    INT_URL = "https://int.api.service.nhs.uk/spine-directory/FHIR/R4"

    # FHIR identifier systems
    ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
    INTERACTION_SYSTEM = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
    PARTYKEY_SYSTEM = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
    ASID_SYSTEM = "https://fhir.nhs.uk/Id/nhsSpineASID"

    # SDS resource types
    DEVICE: Literal["Device"] = "Device"
    ENDPOINT: Literal["Endpoint"] = "Endpoint"

    # Define here so it's neater
    get_method: GetCallable

    # Default service interaction ID for GP Connect
    DEFAULT_SERVICE_INTERACTION_ID = ACCESS_RECORD_STRUCTURED_INTERACTION_ID

    def __init__(
        self,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
        service_interaction_id: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.service_interaction_id = (
            service_interaction_id or self.DEFAULT_SERVICE_INTERACTION_ID
        )
        self.stub = None

        self.api_key = self._get_api_key()

        if os.environ.get("STUB_SDS", None):
            self.stub = SdsFhirApiStub()
            self.get_method = self.stub.get
        else:
            self.get_method = requests.get

    def _build_headers(self, correlation_id: str | None = None) -> dict[str, str]:
        """
        Build mandatory and optional headers for an SDS request.
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
        get_endpoint: bool = True,
    ) -> SdsSearchResults | None:
        """
        Retrieve ASID and endpoint for an organization by ODS code.

        This method performs two SDS queries:
        1. Query /Device to get the ASID for the organization
        2. Query /Endpoint to get the endpoint URL (if available)
        """
        # Step 1: Get Device to obtain ASID
        device_bundle = self._query_sds(
            ods_code=ods_code,
            correlation_id=correlation_id,
            timeout=timeout,
            querytype=self.DEVICE,
        )

        device = self._extract_first_entry(device_bundle)

        # TODO: Post-steel-thread handle case where no device is found for ODS code

        asid = self._extract_identifier(device, self.ASID_SYSTEM)
        party_key = self._extract_identifier(device, self.PARTYKEY_SYSTEM)

        # Step 2: Get Endpoint to obtain endpoint URL
        endpoint_url: str | None = None

        if not get_endpoint:
            return SdsSearchResults(asid=asid, endpoint=None)

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

    @staticmethod
    def _get_api_key() -> str:
        """
        Retrieve the API key to use for SDS requests.

        This is a placeholder at present because we don't have a real API key.
        Ultimately it will probably obtain the key from AWS secrets
        """

        # TODO: Obtain key from AWS secrets
        # DO NOT PUT A REAL KEY HERE, IT WILL BE VISIBLE ON GITHUB
        return "test_api_key_DO_NOT_REPLACE_HERE"

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

        # TODO: Post-steel-thread we probably want a raise_for_status() here

        body = response.json()
        return cast("ResultStructureDict", body)

    @staticmethod
    def _extract_first_entry(
        bundle: ResultStructureDict,
    ) -> ResultStructureDict:  # TODO: Post-steel-thread this may return a None as well
        """
        Extract the first resource from a Bundle.
        """
        entries = cast("ResultList", bundle.get("entry", []))

        # TODO: Post-steel-thread handle case where bundle contains no entries

        # TODO: consider business logic for handling multiple entries in beta
        first_entry = entries[0]
        return cast("ResultStructureDict", first_entry.get("resource", {}))

    def _extract_identifier(
        self, device: ResultStructureDict, system: str
    ) -> str | None:
        """
        Extract an identifier value from a Device resource for a given system.
        """
        identifiers = cast("ResultList", device.get("identifier", []))

        for identifier in identifiers:
            id_system = str(identifier.get("system", ""))
            if id_system == system:
                value = identifier.get("value")
                if value:
                    return str(value).strip()

        return None
