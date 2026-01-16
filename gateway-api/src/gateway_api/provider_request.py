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

# imports

import requests
from requests import Response

# definitions
ars_interactionId = "urn:nhs:names:services:gpconnect:structured:fhir:operation:gpc.getstructuredrecord-1"  # noqa: E501 this is standard InteractionID for accessRecordStructured
ars_fhir_base = "/FHIR/STU3"
ars_fhir_operation = "$gpc.getstructuredrecord"
timeout = None  # None used for quicker dev, adjust as needed


class ExternalServiceError(Exception):
    """
    Exception raised when the downstream GPProvider FHIR API request fails.

    This exception wraps :class:`requests.HTTPError` thrown by
    ``response.raise_for_status()`` and re-raises it as ``ExternalServiceError``
    to decouple callers from the underlying ``requests`` library exception types.
    """


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
        """
        Create a GPProviderClient instance.

        Args:
            provider_endpoint (str): The FHIR API endpoint for the provider.
            provider_asid (str): The ASID for the provider.
            consumer_asid (str): The ASID for the consumer.

        methods:
            access_structured_record: fetch structured patient record
            from GPProvider FHIR API.
        """
        self.provider_endpoint = provider_endpoint
        self.provider_asid = provider_asid
        self.consumer_asid = consumer_asid

    def _build_headers(self, trace_id: str) -> dict[str, str]:
        """
        Build the headers required for the GPProvider FHIR API request.

        Args:
            trace_id (str): A unique identifier for the request.

        Returns:
            dict[str, str]: A dictionary containing the headers for the request,
            including content type, interaction ID, and ASIDs for the provider
            and consumer.
        """
        return {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
            "Ssp-InteractionID": ars_interactionId,
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

        Args:
            trace_id (str): A unique identifier for the request, passed in the headers.
            body (str): The request body in FHIR format.

        Returns:
            Response: The response from the GPProvider FHIR API.

        Raises:
            ExternalServiceError: If the API request fails with an HTTP error.
        """

        headers = self._build_headers(trace_id)

        response = requests.post(
            self.provider_endpoint + ars_fhir_base + "/patient/" + ars_fhir_operation,
            headers=headers,
            data=body,
            timeout=timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise ExternalServiceError(
                f"GPProvider FHIR API request failed:{err.response.reason}"
            ) from err

        return response
