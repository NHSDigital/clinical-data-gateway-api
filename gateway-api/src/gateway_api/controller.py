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
from gateway_api.sds_search import SdsClient, SdsSearchResults


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
        sds_base_url: str = SdsClient.SANDBOX_URL,
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

        try:
            provider_ods = self._get_pds_details(
                auth_token, request.ods_from.strip(), request.nhs_number
            )
        except RequestError as err:
            return FlaskResponse(status_code=err.status_code, data=str(err))

        try:
            consumer_asid, provider_asid, provider_endpoint = self._get_sds_details(
                auth_token, request.ods_from.strip(), provider_ods
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
            trace_id=request.trace_id,
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
            ignore_dates=True,
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

        :param auth_token: Authorization token to use for SDS (used as API key).
        :param consumer_ods: Consumer organisation ODS code (from request headers).
        :param provider_ods: Provider organisation ODS code (from PDS).
        :returns: Tuple of (consumer_asid, provider_asid, provider_endpoint).
        :raises RequestError: If SDS data is missing or incomplete for provider/consumer
        """
        # SDS: Get provider details (ASID + endpoint) for provider ODS
        sds = SdsClient(
            api_key=auth_token,
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
