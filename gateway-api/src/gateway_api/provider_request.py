"""
Module: gateway_api.provider_request

This module contains the GPProvider class, which provides a
simple client for GPProvider FHIR GP System.
The GPProvider class has a sigle method to get_structure_record which
can be used to fetch patient records from a GPProvider FHIR API endpoint.
Usage:

    instantiate a GPProvider with:
            provider_endpoint
            provider_ASID
            consumer_ASID

    method get_structured_record with (may add optional parameters later):
        Parameters: parameters resource

    returns the response from the provider FHIR API.

"""

# imports

import requests
from requests import Response


# definitions
class ExternalServiceError(Exception):
    """
    Raised when the downstream PDS request fails.

    This module catches :class:`requests.HTTPError` thrown by
    ``response.raise_for_status()`` and re-raises it as ``ExternalServiceError`` so
    callers are not coupled to ``requests`` exception types.
    """


class GpProviderClient:
    """
    A simple client for GPProvider FHIR GP System.
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
            provider_asid (str): The ASID for the provider.
            consumer_asid (str): The ASID for the consumer.

        Returns:
            dict: Headers for the request.
        """
        return {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
            "Ssp-InteractionID": "urn:nhs:names:services:gpconnect:structured:fhir:operation:gpc.getstructuredrecord-1",  # noqa: E501 this is standard InteractionID for accessRecordStructured
            "Ssp-To": self.provider_asid,
            "Ssp-From": self.consumer_asid,
            "Ssp-TraceID": trace_id,
        }

    def access_structured_record(
        self,
        trace_id: str,  # from consumer header
        body: str,  # forwarded from consumer_request
        # nhsnumber: str, # from request
    ) -> Response:
        """
        Fetch a structured patient record from the GPProvider FHIR API.

        Args:
            parameters (dict): The parameters resource to send in the request.
        returns:
            dict: The response from the GPProvider FHIR API.
        """

        headers = self._build_headers(trace_id)

        response = requests.post(
            self.provider_endpoint,
            headers=headers,
            data=body,
            timeout=None,  # noqa: S113 quicker dev cycle; adjust as needed
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise ExternalServiceError(
                f"GPProvider FHIR API request failed:{err.response.reason}"
            ) from err

        return response
