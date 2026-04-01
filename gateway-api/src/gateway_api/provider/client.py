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

from gateway_api.clinical_jwt import JWT, JWTValidator
from gateway_api.common.common import get_http_text
from gateway_api.common.error import JWTValidationError, ProviderRequestFailedError
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

# Default endpoint path for access record structured interaction (standard GP Connect)
ARS_ENDPOINT_PATH = "Patient/$gpc.getstructuredrecord"
TIMEOUT: int | None = None  # None used for quicker dev, adjust as needed


class GpProviderClient:
    """
    A client for interacting with the GPProvider FHIR GP System.

    This class provides methods to interact with the GPProvider FHIR API,
    including fetching structured patient records.

    Attributes:
        provider_endpoint (str): The base URL for the provider (from SDS).
        provider_asid (str): The ASID for the provider.
        consumer_asid (str): The ASID for the consumer.
        token (JWT): JWT object for authentication with the provider API.
        endpoint_path (str): The endpoint path for the operation
            (default: "Patient/$gpc.getstructuredrecord").

    Methods:
        access_structured_record(trace_id: str, body: str) -> Response:
            Fetch a structured patient record from the GPProvider FHIR API.
    """

    def __init__(
        self,
        provider_endpoint: str,
        provider_asid: str,
        consumer_asid: str,
        token: JWT,
        endpoint_path: str = ARS_ENDPOINT_PATH,
    ) -> None:
        self.provider_endpoint = provider_endpoint
        self.provider_asid = provider_asid
        self.consumer_asid = consumer_asid
        self.token = token
        self.endpoint_path = endpoint_path

    def _build_headers(self, trace_id: str) -> dict[str, str]:
        """
        Build the headers required for the GPProvider FHIR API request.
        """
        # Re-check the JWT is still valid, in case has expired since
        # client instantiation
        try:
            JWTValidator.validate_timestamps(self.token)
        except JWTValidationError as e:
            raise ProviderRequestFailedError(error_reason="JWT has expired") from e
        return {
            "Content-Type": "application/fhir+json; charset=utf-8",
            "Accept": "application/fhir+json; charset=utf-8",
            "Ssp-InteractionID": ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            "Ssp-To": self.provider_asid,
            "Ssp-From": self.consumer_asid,
            "Ssp-TraceID": trace_id,
            "Authorization": f"Bearer {self.token}",
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

        base_endpoint = self.provider_endpoint.rstrip("/") + "/"
        url = urljoin(base_endpoint, self.endpoint_path)

        response = post(
            url,
            headers=headers,
            data=body,
            timeout=TIMEOUT,
        )

        try:
            response.raise_for_status()
        except HTTPError as err:
            # TODO: Consider what error information we want to return here.
            #   Post-steel-thread we probably want to log rather than dumping like this
            if os.environ.get("CDG_DEBUG", "false").lower() == "true":
                errstr = "GPProvider FHIR API request failed:\n"
                errstr += f"{response.status_code}: "
                errstr += f"{get_http_text(response.status_code)}:{response.reason}\n"
                errstr += response.text
                errstr += "\nHeaders were:\n"
                for header, value in headers.items():
                    errstr += f"{header}: {value}\n"
                errstr += "\nBody payload was:\n"
                errstr += body
            else:
                errstr = str(err.response.reason)
            raise ProviderRequestFailedError(error_reason=errstr) from err

        return response

    @property
    def token(self) -> JWT:
        return self._token

    @token.setter
    def token(self, jwt_obj: JWT) -> None:
        """
        Set the JWT token, validating its structure and contents.
        """
        # If JWT validation fails allow the error to propagate up,
        # the caller needs to know it passed an invalid JWT and why.
        JWTValidator.validate(jwt_obj)
        self._token = jwt_obj
