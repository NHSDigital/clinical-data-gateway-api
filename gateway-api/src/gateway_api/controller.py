from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import requests

from src.gateway_api.common.common import FlaskResponse, validate_nhs_number
from src.gateway_api.pds_search import PdsClient, SearchResults


class DownstreamServiceError(RuntimeError):
    """Raised when a downstream dependency (PDS/SDS/GP Connect) fails."""


@dataclass
class SdsSearchResults:
    """
    Stub SDS search results dataclass.
    Replace this with the real one once it's implemented.
    """

    asid: str


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

    def get_asid(self, ods_code: str) -> SdsSearchResults | None:
        # Placeholder implementation
        return SdsSearchResults(asid=f"asid_{ods_code}")


class GpConnectClient:
    """
    Stub GP Connect client for obtaining patient records.
    Replace this with the real one once it's implemented.
    """

    SANDBOX_URL = "https://example.invalid/gpconnect"

    def __init__(
        self,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def get_patient_records(
        self,
        nhs_number: str,  # NOSONAR S1172 (ignore in stub)
        asid: str,  # NOSONAR S1172 (ignore in stub)
        auth_token: str,  # NOSONAR S1172 (ignore in stub)
    ) -> requests.Response | None:
        # Placeholder implementation
        return None


class Controller:
    """
    Orchestrates calls to PDS -> SDS -> GP Connect.

    Entry point:
        - call_gp_connect(nhs_number, auth_token) -> requests.Response
    """

    def __init__(
        self,
        # PDS configuration
        pds_end_user_org_ods: str,
        pds_base_url: str = PdsClient.SANDBOX_URL,
        nhsd_session_urid: str | None = None,
        timeout: int = 10,
        sds_base_url: str = "https://example.invalid/sds",
        gp_connect_base_url: str = "https://example.invalid/gpconnect",
    ) -> None:
        self.pds_end_user_org_ods = pds_end_user_org_ods
        self.pds_base_url = pds_base_url
        self.sds_base_url = sds_base_url
        self.nhsd_session_urid = nhsd_session_urid
        self.timeout = timeout

        self.sds_client = SdsClient(base_url=sds_base_url, timeout=timeout)
        self.gp_connect_client = GpConnectClient(
            base_url=gp_connect_base_url, timeout=timeout
        )

    def call_gp_connect(
        self,
        nhs_number: str | int,
        auth_token: str,
    ) -> FlaskResponse:
        """
        1) Call PDS to obtain the patient's GP ODS code.
        2) Call SDS to obtain ASID (using ODS code + auth token).
        3) Call GP Connect to obtain patient records

        """
        nhs_number_int = _coerce_nhs_number_to_int(nhs_number)
        nhs_number_str = str(nhs_number_int)

        # --- PDS: find patient and extract GP ODS code ---
        pds = PdsClient(
            auth_token=auth_token,
            end_user_org_ods=self.pds_end_user_org_ods,
            base_url=self.pds_base_url,
            nhsd_session_urid=self.nhsd_session_urid,
            timeout=self.timeout,
        )

        pds_result: SearchResults | None = pds.search_patient_by_nhs_number(
            nhs_number_int
        )

        if pds_result is None:
            return FlaskResponse(
                status_code=404,
                data=f"No PDS patient found for NHS number {nhs_number_str}",
            )

        ods_code = (pds_result.gp_ods_code or "").strip()
        if not ods_code:
            return FlaskResponse(
                status_code=404,
                data=(
                    f"PDS patient {nhs_number_str} did not contain a current "
                    "GP ODS code"
                ),
            )

        # --- SDS: Get ASID for given GP practice ---
        sds = SdsClient(
            auth_token=auth_token,
            base_url=self.sds_base_url,
            timeout=self.timeout,
        )

        sds_result: SdsSearchResults | None = sds.get_asid(ods_code)

        if sds_result is None:
            return FlaskResponse(
                status_code=404,
                data=f"No ASID found for ODS code {ods_code}",
            )

        asid = (sds_result.asid or "").strip()
        if not asid:
            return FlaskResponse(
                status_code=404,
                data=(
                    f"SDS result for ODS code {ods_code} did not contain a current ASID"
                ),
            )

        # --- Call GP Connect with given NHS number and ASID ---
        response = self.gp_connect_client.get_patient_records(
            nhs_number=nhs_number_str,
            asid=asid,
            auth_token=auth_token,
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
