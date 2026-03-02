"""
Module: gateway_api.provider_request

This module contains the GpProviderClient class, which provides a
simple client for interacting with the GPProvider FHIR GP System.

The GpProviderClient class includes methods to fetch structured patient
records from a GPProvider FHIR API endpoint.

Usage:
    Instantiate a GpProviderClient with:
        - provider_endpoint: The FHIR API endpoint for the provider.
        - provider_asid: The ASID for the provider.
        - consumer_asid: The ASID for the consumer.

    Use the `access_structured_record` method to fetch a structured patient record:
        Parameters:
            - trace_id (str): A unique identifier for the request.
            - body (str): The request body in FHIR format.

    Returns:
        The response from the provider FHIR API.
"""

import os
from urllib.parse import urljoin

from requests import HTTPError, Response

from gateway_api.common.error import ProviderRequestFailedError
from gateway_api.get_structured_record import ACCESS_RECORD_STRUCTURED_INTERACTION_ID

# TODO: Once stub servers/containers made for PDS, SDS and provider
#       we should remove the STUB_PROVIDER environment variable and just
#       use the stub client
STUB_PROVIDER = os.environ.get("STUB_PROVIDER", "false").lower() == "true"
if not STUB_PROVIDER:
    from requests import post
else:
    from stubs.provider.stub import GpProviderStub

    provider_stub = GpProviderStub()
    post = provider_stub.post  # type: ignore

ARS_FHIR_BASE = "FHIR/STU3"
FHIR_RESOURCE = "patient"
ARS_FHIR_OPERATION = "$gpc.getstructuredrecord"
TIMEOUT: int | None = None  # None used for quicker dev, adjust as needed


class GpProviderClient:
    """
    A client for interacting with the GPProvider FHIR GP System.

    This class provides methods to interact with the GPProvider FHIR API,
    including fetching structured patient records.

    Attributes:
        provider_endpoint (str): The FHIR API endpoint for the provider.
        provider_asid (str): The ASID for the provider.
        consumer_asid (str): The ASID for the consumer.

    Methods:
        access_structured_record(trace_id: str, body: str) -> Response:
            Fetch a structured patient record from the GPProvider FHIR API.
    """

    def __init__(
        self,
        provider_endpoint: str,
        provider_asid: str,
        consumer_asid: str,
    ) -> None:
        self.provider_endpoint = provider_endpoint
        self.provider_asid = provider_asid
        self.consumer_asid = consumer_asid

    def _build_headers(self, trace_id: str) -> dict[str, str]:
        """
        Build the headers required for the GPProvider FHIR API request.
        """
        return {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
            "Ssp-InteractionID": ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            "Ssp-To": self.provider_asid,
            "Ssp-From": self.consumer_asid,
            "Ssp-TraceID": trace_id,
        }

    def access_structured_record(
        self,
        trace_id: str,
        body: str,
    ) -> Response:
        """
        Fetch a structured patient record from the GPProvider FHIR API.
        """

        headers = self._build_headers(trace_id)

        endpoint_path = "/".join([ARS_FHIR_BASE, FHIR_RESOURCE, ARS_FHIR_OPERATION])
        url = urljoin(self.provider_endpoint, endpoint_path)

        response = post(
            url,
            headers=headers,
            data=body,
            timeout=TIMEOUT,
        )

        try:
            response.raise_for_status()
        except HTTPError as err:
            raise ProviderRequestFailedError(error_reason=err.response.reason) from err

        return response
