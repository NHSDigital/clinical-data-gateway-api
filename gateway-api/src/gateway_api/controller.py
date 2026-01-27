"""
Controller layer for orchestrating calls to external services
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from gateway_api.provider_request import GpProviderClient

if TYPE_CHECKING:
    from gateway_api.get_structured_record.request import GetStructuredRecordRequest

__all__ = ["json"]  # Make mypy happy in tests

from dataclasses import dataclass

from gateway_api.common.common import FlaskResponse
from gateway_api.pds_search import PdsClient, PdsSearchResults


@dataclass
class RequestError(Exception):
    """
    Raised (and handled) when there is a problem with the incoming request.

    Instances of this exception are caught by controller entry points and converted
    into an appropriate :class:`FlaskResponse`.

    :param status_code: HTTP status code that should be returned.
    :param message: Human-readable error message.
    """

    status_code: int
    message: str

    def __str__(self) -> str:
        """
        Coercing this exception to a string returns the error message.

        :returns: The error message.
        """
        return self.message


@dataclass
class SdsSearchResults:
    """
    Stub SDS search results dataclass.

    Replace this with the real one once it's implemented.

    :param asid: Accredited System ID.
    :param endpoint: Endpoint URL associated with the organisation, if applicable.
    """

    asid: str
    endpoint: str | None


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

        :param auth_token: Authentication token to present to SDS.
        :param base_url: Base URL for SDS.
        :param timeout: Timeout in seconds for SDS calls.
        """
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        """
        Retrieve SDS org details for a given ODS code.

        This is a placeholder implementation that always returns an ASID and endpoint.

        :param ods_code: ODS code to look up.
        :returns: SDS search results or ``None`` if not found.
        """
        # Placeholder implementation
        return SdsSearchResults(
            asid=f"asid_{ods_code}", endpoint="https://example-provider.org/endpoint"
        )


class Controller:
    """
    Orchestrates calls to PDS -> SDS -> GP provider.

    Entry point:
        - ``call_gp_provider(request_body_json, headers, auth_token) -> FlaskResponse``
    """

    gp_provider_client: GpProviderClient | None

    def __init__(
        self,
        pds_base_url: str = PdsClient.SANDBOX_URL,
        sds_base_url: str = "https://example.invalid/sds",
        nhsd_session_urid: str | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Create a controller instance.

        :param pds_base_url: Base URL for PDS client.
        :param sds_base_url: Base URL for SDS client.
        :param nhsd_session_urid: Session URID for NHS Digital session handling.
        :param timeout: Timeout in seconds for downstream calls.
        """
        self.pds_base_url = pds_base_url
        self.sds_base_url = sds_base_url
        self.nhsd_session_urid = nhsd_session_urid
        self.timeout = timeout
        self.gp_provider_client = None

    def run(self, request: GetStructuredRecordRequest) -> FlaskResponse:
        """
        Controller entry point

        Expects a GetStructuredRecordRequest instance that contains the header and body
        details of the HTTP request received

        Orchestration steps:
        1) Call PDS to obtain the patient's GP (provider) ODS code.
        2) Call SDS using provider ODS to obtain provider ASID + provider endpoint.
        3) Call SDS using consumer ODS to obtain consumer ASID.
        4) Call GP provider to obtain patient records.

        :param request: A GetStructuredRecordRequest instance.
        :returns: A :class:`~gateway_api.common.common.FlaskResponse` representing the
            outcome.
        """
        auth_token = self.get_auth_token()

        if not request.ods_from:
            return FlaskResponse(
                status_code=400,
                data='Missing required header "Ods-from"',
            )

        trace_id = request.trace_id
        if trace_id is None:
            return FlaskResponse(
                status_code=400, data="Missing required header: Ssp-TraceID"
            )

        try:
            provider_ods = self._get_pds_details(
                auth_token, request.ods_from, request.nhs_number
            )
        except RequestError as err:
            return FlaskResponse(status_code=err.status_code, data=str(err))

        try:
            consumer_asid, provider_asid, provider_endpoint = self._get_sds_details(
                auth_token, request.ods_from, provider_ods
            )
        except RequestError as err:
            return FlaskResponse(status_code=err.status_code, data=str(err))

        # Call GP provider with correct parameters
        self.gp_provider_client = GpProviderClient(
            provider_endpoint=provider_endpoint,
            provider_asid=provider_asid,
            consumer_asid=consumer_asid,
        )

        response = self.gp_provider_client.access_structured_record(
            trace_id=trace_id,
            body=request.request_body,
        )

        # If we get a None from the GP provider, that means that either the service did
        # not respond or we didn't make the request to the service in the first place.
        # Therefore a None is a 502, any real response just pass straight back.
        return FlaskResponse(
            status_code=response.status_code if response is not None else 502,
            data=response.text if response is not None else "GP provider service error",
            headers=dict(response.headers) if response is not None else None,
        )

    def get_auth_token(self) -> str:
        """
        Retrieve the authorization token.

        This is a placeholder implementation. Replace with actual logic to obtain
        the auth token as needed.

        :returns: Authorization token as a string.
        """
        # Placeholder implementation
        return "PLACEHOLDER_AUTH_TOKEN"

    def _get_pds_details(
        self, auth_token: str, consumer_ods: str, nhs_number: str
    ) -> str:
        """
        Call PDS to find the provider ODS code (GP ODS code) for a patient.

        :param auth_token: Authorization token to use for PDS.
        :param consumer_ods: Consumer organisation ODS code (from request headers).
        :param nhs_number: NHS number
        :returns: Provider ODS code (GP ODS code).
        :raises RequestError: If the patient cannot be found or has no provider ODS code
        """
        # PDS: find patient and extract GP ODS code (provider ODS)
        pds = PdsClient(
            auth_token=auth_token,
            end_user_org_ods=consumer_ods,
            base_url=self.pds_base_url,
            nhsd_session_urid=self.nhsd_session_urid,
            timeout=self.timeout,
        )

        pds_result: PdsSearchResults | None = pds.search_patient_by_nhs_number(
            nhs_number
        )

        if pds_result is None:
            raise RequestError(
                status_code=404,
                message=f"No PDS patient found for NHS number {nhs_number}",
            )

        if pds_result.gp_ods_code:
            provider_ods_code = pds_result.gp_ods_code
        else:
            raise RequestError(
                status_code=404,
                message=(
                    f"PDS patient {nhs_number} did not contain a current "
                    "provider ODS code"
                ),
            )

        return provider_ods_code

    def _get_sds_details(
        self, auth_token: str, consumer_ods: str, provider_ods: str
    ) -> tuple[str, str, str]:
        """
        Call SDS to obtain consumer ASID, provider ASID, and provider endpoint.

        This method performs two SDS lookups:
        - provider details (ASID + endpoint)
        - consumer details (ASID)

        :param auth_token: Authorization token to use for SDS.
        :param consumer_ods: Consumer organisation ODS code (from request headers).
        :param provider_ods: Provider organisation ODS code (from PDS).
        :returns: Tuple of (consumer_asid, provider_asid, provider_endpoint).
        :raises RequestError: If SDS data is missing or incomplete for provider/consumer
        """
        # SDS: Get provider details (ASID + endpoint) for provider ODS
        sds = SdsClient(
            auth_token=auth_token,
            base_url=self.sds_base_url,
            timeout=self.timeout,
        )

        provider_details: SdsSearchResults | None = sds.get_org_details(provider_ods)
        if provider_details is None:
            raise RequestError(
                status_code=404,
                message=f"No SDS org found for provider ODS code {provider_ods}",
            )

        provider_asid = (provider_details.asid or "").strip()
        if not provider_asid:
            raise RequestError(
                status_code=404,
                message=(
                    f"SDS result for provider ODS code {provider_ods} did not contain "
                    "a current ASID"
                ),
            )

        provider_endpoint = (provider_details.endpoint or "").strip()
        if not provider_endpoint:
            raise RequestError(
                status_code=404,
                message=(
                    f"SDS result for provider ODS code {provider_ods} did not contain "
                    "a current endpoint"
                ),
            )

        # SDS: Get consumer details (ASID) for consumer ODS
        consumer_details: SdsSearchResults | None = sds.get_org_details(consumer_ods)
        if consumer_details is None:
            raise RequestError(
                status_code=404,
                message=f"No SDS org found for consumer ODS code {consumer_ods}",
            )

        consumer_asid = (consumer_details.asid or "").strip()
        if not consumer_asid:
            raise RequestError(
                status_code=404,
                message=(
                    f"SDS result for consumer ODS code {consumer_ods} did not contain "
                    "a current ASID"
                ),
            )

        return consumer_asid, provider_asid, provider_endpoint
