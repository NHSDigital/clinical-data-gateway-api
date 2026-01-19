from __future__ import annotations

import json

__all__ = ["json"]  # Make mypy happy in tests

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    import requests

from gateway_api.common.common import FlaskResponse, json_str, validate_nhs_number
from gateway_api.pds_search import PdsClient, PdsSearchResults


class DownstreamServiceError(RuntimeError):
    """Raised when a downstream dependency (PDS/SDS/GP Connect) fails."""


@dataclass
class RequestError(Exception):
    """Raised (and handled) when there is a problem with the incoming request."""

    status_code: int
    message: str

    def __str__(self) -> str:
        return self.message


@dataclass
class SdsSearchResults:
    """
    Stub SDS search results dataclass.
    Replace this with the real one once it's implemented.
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
        auth_token: str | None = None,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
    ) -> None:
        self.auth_token = auth_token
        self.base_url = base_url
        self.timeout = timeout

    def get_org_details(self, ods_code: str) -> SdsSearchResults | None:
        # Placeholder implementation
        return SdsSearchResults(
            asid=f"asid_{ods_code}", endpoint="https://example-provider.org/endpoint"
        )


class GpConnectClient:
    """
    Stub GP Connect client for obtaining patient records.
    Replace this with the real one once it's implemented.
    """

    SANDBOX_URL = "https://example.invalid/gpconnect"

    def __init__(
        self,
        provider_endpoint: str,  # Obtain from ODS
        provider_asid: str,
        consumer_asid: str,
    ) -> None:
        self.provider_endpoint = provider_endpoint
        self.provider_asid = provider_asid
        self.consumer_asid = consumer_asid

    def access_structured_record(
        self,
        trace_id: str,  # NOSONAR S1172 (ignore in stub)
        body: json_str,  # NOSONAR S1172 (ignore in stub)
        nhsnumber: str,  # NOSONAR S1172 (ignore in stub)
    ) -> requests.Response | None:
        # Placeholder implementation
        return None


class Controller:
    """
    Orchestrates calls to PDS -> SDS -> GP Connect.

    Entry point:
        - call_gp_connect(request_body_json, headers, auth_token) -> requests.Response
    """

    # TODO: Un-AI the docstrings and comments

    gp_connect_client: GpConnectClient | None

    def __init__(
        self,
        pds_base_url: str = PdsClient.SANDBOX_URL,
        sds_base_url: str = "https://example.invalid/sds",
        nhsd_session_urid: str | None = None,
        timeout: int = 10,
    ) -> None:
        self.pds_base_url = pds_base_url
        self.sds_base_url = sds_base_url
        self.nhsd_session_urid = nhsd_session_urid
        self.timeout = timeout

        self.sds_client = SdsClient(base_url=sds_base_url, timeout=timeout)
        self.gp_connect_client = None

    def _get_details_from_body(self, request_body: json_str) -> int:
        # --- Extract NHS number from request body ---
        try:
            body: Any = json.loads(request_body)
        except (TypeError, json.JSONDecodeError):
            raise RequestError(
                status_code=400,
                message='Request body must be valid JSON with an "nhs-number" field',
            ) from None

        if not hasattr(body, "getitem"):  # Must be a dict-like object
            raise RequestError(
                status_code=400,
                message='Request body must be a JSON object with an "nhs-number" field',
            ) from None

        nhs_number_value = body.get("nhs-number")
        if nhs_number_value is None:
            raise RequestError(
                status_code=400,
                message='Missing required field "nhs-number" in JSON request body',
            ) from None

        try:
            nhs_number_int = _coerce_nhs_number_to_int(nhs_number_value)
        except ValueError:
            raise RequestError(
                status_code=400,
                message=(
                    f'Could not coerce NHS number "{nhs_number_value}" to an integer'
                ),
            ) from None

        return nhs_number_int

    def _get_pds_details(
        self, auth_token: str, consumer_ods: str, nhs_number: int
    ) -> str:
        # --- PDS: find patient and extract GP ODS code (provider ODS) ---
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
        # --- SDS: Get provider details (ASID + endpoint) for provider ODS ---
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

        # --- SDS: Get consumer details (ASID) for consumer ODS ---
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

    def call_gp_connect(
        self,
        request_body: json_str,
        headers: dict[str, str],
        auth_token: str,
    ) -> FlaskResponse:
        """
        Expects a JSON request body containing an "nhs-number" field.
        Also expects HTTP headers (from Flask) and extracts "Ods-from" as consumer_ods.

        1) Call PDS to obtain the patient's GP (provider) ODS code.
        2) Call SDS using provider ODS to obtain provider ASID + provider endpoint.
        3) Call SDS using consumer ODS to obtain consumer ASID.
        4) Call GP Connect to obtain patient records
        """

        try:
            nhs_number = self._get_details_from_body(request_body)
        except RequestError as err:
            return FlaskResponse(
                status_code=err.status_code,
                data=str(err),
            )

        # --- Extract consumer ODS from headers ---
        consumer_ods = headers.get("Ods-from", "").strip()
        if not consumer_ods:
            return FlaskResponse(
                status_code=400,
                data='Missing required header "Ods-from"',
            )

        trace_id = headers.get("X-Request-ID")
        if trace_id is None:
            return FlaskResponse(
                status_code=400, data="Missing required header: X-Request-ID"
            )

        try:
            provider_ods = self._get_pds_details(auth_token, consumer_ods, nhs_number)
        except RequestError as err:
            return FlaskResponse(status_code=err.status_code, data=str(err))

        try:
            consumer_asid, provider_asid, provider_endpoint = self._get_sds_details(
                auth_token, consumer_ods, provider_ods
            )
        except RequestError as err:
            return FlaskResponse(status_code=err.status_code, data=str(err))

        # --- Call GP Connect with correct parameters ---
        # (If these are dynamic per-request, reinitialise the client accordingly.)
        self.gp_connect_client = GpConnectClient(
            provider_endpoint=provider_endpoint,
            provider_asid=provider_asid,
            consumer_asid=consumer_asid,
        )

        response = self.gp_connect_client.access_structured_record(
            trace_id=trace_id,
            body=request_body,
            nhsnumber=str(nhs_number),
        )

        return FlaskResponse(
            status_code=response.status_code if response else 502,
            data=response.text if response else "GP Connect service error",
            headers=dict(response.headers) if response else None,
        )


def _coerce_nhs_number_to_int(value: str | int) -> int:
    """
    Coerce NHS number to int with basic validation.
    NHS numbers are 10 digits, but leading zeros are not typically used.
    Adjust validation as needed for your domain rules.
    """
    try:
        stripped = cast("str", value).strip().replace(" ", "")
    except AttributeError:
        nhs_number_int = cast("int", value)
    else:
        if not stripped.isdigit():
            raise ValueError("NHS number must be numeric")
        nhs_number_int = int(stripped)

    if len(str(nhs_number_int)) != 10:
        # If you need to accept test numbers of different length, relax this.
        raise ValueError("NHS number must be 10 digits")

    if not validate_nhs_number(nhs_number_int):
        raise ValueError("NHS number is invalid")

    return nhs_number_int
