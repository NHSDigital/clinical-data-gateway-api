"""
SDS (Spine Directory Service) FHIR R4 device and endpoint lookup client.

This module provides a client for querying the Spine Directory Service to retrieve:
- Device records (including ASID - Accredited System ID)
- Endpoint records (including endpoint URLs for routing)
"""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Any

from fhir import Resource
from fhir.constants import FHIRSystem
from fhir.r4 import Bundle, Device, Endpoint

from gateway_api.get_structured_record import ACCESS_RECORD_STRUCTURED_INTERACTION_ID
from gateway_api.sds.search_results import SdsSearchResults

# TODO: Once stub servers/containers made for PDS, SDS and provider
#       we should remove the STUB_SDS environment variable and just
#       use the stub client
STUB_SDS = os.environ.get("STUB_SDS", "false").lower() == "true"
if not STUB_SDS:
    from requests import get
else:
    from stubs import SdsFhirApiStub

    sds = SdsFhirApiStub()
    get = sds.get  # type: ignore


class SdsResourceType(StrEnum):
    """SDS FHIR resource types."""

    DEVICE = "Device"
    ENDPOINT = "Endpoint"


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
        self.api_key = self._get_api_key()

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
    ) -> SdsSearchResults:
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
            querytype=SdsResourceType.DEVICE,
        )

        device = self._extract_first_resource(device_bundle, Device)

        if not device:
            empty_search_results = SdsSearchResults(asid=None, endpoint=None)
            return empty_search_results

        asid = self._extract_device_identifier(device, FHIRSystem.NHS_SPINE_ASID)
        party_key = self._extract_device_identifier(
            device, FHIRSystem.NHS_MHS_PARTY_KEY
        )

        # Step 2: Get Endpoint to obtain endpoint URL
        endpoint_url: str | None = None

        if not get_endpoint:
            return SdsSearchResults(asid=asid, endpoint=None)

        endpoint_bundle = self._query_sds(
            ods_code=ods_code,
            party_key=party_key,
            correlation_id=correlation_id,
            timeout=timeout,
            querytype=SdsResourceType.ENDPOINT,
        )
        endpoint = self._extract_first_resource(endpoint_bundle, Endpoint)
        if endpoint and endpoint.address:
            endpoint_url = str(endpoint.address).strip()

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
        querytype: SdsResourceType = SdsResourceType.DEVICE,
    ) -> Bundle:
        """
        Query SDS /Device or /Endpoint endpoint.
        """
        headers = self._build_headers(correlation_id=correlation_id)
        url = f"{self.base_url}/{querytype.value}"

        params: dict[str, Any] = {
            "organization": f"{FHIRSystem.ODS_CODE}|{ods_code}",
            "identifier": [
                f"{FHIRSystem.NHS_SERVICE_INTERACTION_ID}|{self.service_interaction_id}"
            ],
        }

        if party_key is not None:
            params["identifier"].append(f"{FHIRSystem.NHS_MHS_PARTY_KEY}|{party_key}")

        response = get(
            url,
            headers=headers,
            params=params,
            timeout=timeout or self.timeout,
        )

        # TODO: Post-steel-thread we probably want a raise_for_status() here

        bundle = Bundle.model_validate(response.json())
        return bundle

    @staticmethod
    def _extract_first_resource[T: Resource](
        bundle: Bundle, resource: type[T]
    ) -> T | None:
        # TODO: Post-steel-thread handle case where bundle contains no entries

        # TODO: more carefully consider business logic for handling multiple
        #       entries in beta
        resources = bundle.find_resources(resource)
        if not resources:
            return None
        first_entry = resources[0]
        return first_entry

    def _extract_device_identifier(self, device: Device, system: str) -> str | None:
        """
        Extract an identifier value from a Device resource for a given system.
        """
        for identifier in device.identifier:
            if identifier.system == system:
                return identifier.value

        return None
