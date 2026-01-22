from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import requests

# Recursive JSON-like structure typing (mirrors the approach in pds_search.py).
ResultStructure = (
    str
    | int
    | float
    | bool
    | None
    | dict[str, "ResultStructure"]
    | list["ResultStructure"]
)
ResultStructureDict = dict[str, ResultStructure]
ResultList = list[ResultStructureDict]


class ExternalServiceError(Exception):
    """
    Raised when the downstream SDS request fails.

    Wraps requests.HTTPError so callers are not coupled to requests exception types.
    """


@dataclass(frozen=True)
class DeviceLookupResult:
    """
    Result of an SDS /Device lookup.

    :param asid: Accredited System Identifier (ASID), if found.
    :param endpoint_url: Endpoint URL, if found.
    """

    asid: str | None
    endpoint_url: str | None


class SdsClient:
    """
    Simple client for SDS FHIR R4 /Device lookup.

    Calls GET /Device (returns a FHIR Bundle) and extracts:
        - ASID from Device.identifier[].value
        - Endpoint URL from Device.extension[] (best-effort)

    Notes:
    - /Device requires both 'organization' and 'identifier' query params.
    - 'identifier' must include a service interaction ID; may also include an MHS party
        key.
    """

    SANDBOX_URL = "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4"
    INT_URL = "https://int.api.service.nhs.uk/spine-directory/FHIR/R4"
    DEP_UAT_URL = "https://dep.api.service.nhs.uk/spine-directory/FHIR/R4"
    PROD_URL = "https://api.service.nhs.uk/spine-directory/FHIR/R4"

    # Default taken from the OpenAPI example. In real usage you should pass the
    # interaction ID relevant to the service you are routing to.
    DEFAULT_SERVICE_INTERACTION_ID = "urn:nhs:names:services:psis:REPC_IN150016UK05"

    ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
    INTERACTION_SYSTEM = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
    PARTYKEY_SYSTEM = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"

    def __init__(
        self,
        api_key: str,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
    ) -> None:
        """
        :param api_key: SDS subscription key value (header 'apikey'). In Sandbox, any
            value works.
        :param base_url: Base URL for the SDS API. Trailing slashes are stripped.
        :param timeout: Default timeout in seconds for HTTP calls.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _build_headers(self, correlation_id: str | None = None) -> dict[str, str]:
        headers = {
            "Accept": "application/fhir+json",
            "apikey": self.api_key,
        }
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        return headers

    def lookup_device_asid_and_endpoint(
        self,
        device_ods_code: str,
        service_interaction_id: str | None = None,
        party_key: str | None = None,
        manufacturing_ods_code: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> DeviceLookupResult:
        """
        Look up an accredited system by organisation ODS code plus service interaction
        ID (and optionally party key/manufacturing org), returning ASID and endpoint URL

        :param device_ods_code: ODS code used in the required 'organization' query
            parameter.
        :param service_interaction_id: Interaction ID for the target service (required
            by SDS /Device). If not supplied, a default from the OpenAPI example is used
        :param party_key: Optional MHS party key (included as a second 'identifier'
            occurrence).
        :param manufacturing_ods_code: Optional manufacturing organisation ODS code.
        :param correlation_id: Optional correlation ID for tracing.
        :param timeout: Optional per-call timeout in seconds.
        """
        bundle = self._get_device_bundle(
            organization_ods=device_ods_code,
            service_interaction_id=service_interaction_id
            or self.DEFAULT_SERVICE_INTERACTION_ID,
            party_key=party_key,
            manufacturing_ods=manufacturing_ods_code,
            correlation_id=correlation_id,
            timeout=timeout,
        )

        entries = cast("list[dict[str, Any]]", bundle.get("entry", []))
        if not entries:
            return DeviceLookupResult(asid=None, endpoint_url=None)

        # Best-effort: return first entry that yields an ASID; else fall back to first
        # TODO: Look at this again. If we don't get a hit then should return None
        best: DeviceLookupResult | None = None
        for entry in entries:
            device = cast("dict[str, Any]", entry.get("resource", {}))
            asid = self._extract_asid(device)
            endpoint_url = self._extract_endpoint_url(device)
            candidate = DeviceLookupResult(asid=asid, endpoint_url=endpoint_url)
            if asid:
                return candidate
            best = best or candidate

        return best or DeviceLookupResult(asid=None, endpoint_url=None)

    def _get_device_bundle(
        self,
        organization_ods: str,
        service_interaction_id: str,
        party_key: str | None,
        manufacturing_ods: str | None,
        correlation_id: str | None,
        timeout: int | None,
    ) -> dict[str, Any]:
        headers = self._build_headers(correlation_id=correlation_id)

        url = f"{self.base_url}/Device"

        params: dict[str, Any] = {
            "organization": f"{self.ODS_SYSTEM}|{organization_ods}",
            # Explode=true means repeating identifier=... is acceptable; requests
            # will encode a list as repeated query params.
            "identifier": [f"{self.INTERACTION_SYSTEM}|{service_interaction_id}"],
        }

        if party_key:
            params["identifier"].append(f"{self.PARTYKEY_SYSTEM}|{party_key}")

        if manufacturing_ods:
            params["manufacturing-organization"] = (
                f"{self.ODS_SYSTEM}|{manufacturing_ods}"
            )

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout or self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise ExternalServiceError(
                f"SDS /Device request failed: {err.response.status_code} "
                f"{err.response.reason}"
            ) from err

        body = response.json()
        return cast("dict[str, Any]", body)

    @staticmethod
    def _extract_asid(device: dict[str, Any]) -> str | None:
        """
        ASID is described by the caller as: "the value field in the identifier array".

        The schema is generic (identifier[] elements are {system, value}), so this uses
        a best-effort heuristic:
            1) Prefer an identifier whose system mentions 'asid'
            2) Else return the first identifier.value present
        """
        # TODO: No, just take identifier.value, not system
        # TODO: But check that identifier.value is actually the ASID
        identifiers = cast("list[dict[str, Any]]", device.get("identifier", []))
        if not identifiers:
            return None

        def value_of(item: dict[str, Any]) -> str | None:
            v = item.get("value")
            return str(v).strip() if v is not None and str(v).strip() else None

        # TODO: No!
        # Prefer system containing "asid"
        for ident in identifiers:
            system = str(ident.get("system", "") or "").lower()
            if "asid" in system:
                v = value_of(ident)
                if v:
                    return v

        # TODO: Also No!
        # Fallback: first non-empty value
        for ident in identifiers:
            v = value_of(ident)
            if v:
                return v

        return None

    @staticmethod
    def _extract_endpoint_url(device: dict[str, Any]) -> str | None:
        """
        The caller asked for: "endpoint URL, which is the 'url' field in the 'extension'
        array".

        In the schema, each extension item has:
            - url
            - valueReference.identifier.{system,value}

        Best-effort strategy:
            1) If valueReference.identifier.value looks like a URL, return that
            2) Else return extension.url if it looks like a URL
        """
        # TODO: Stupid AI. I said extension.url, not identifier.value
        extensions = cast("list[dict[str, Any]]", device.get("extension", []))
        if not extensions:
            return None

        def looks_like_url(s: str) -> bool:
            return s.startswith("http://") or s.startswith("https://")

        for ext in extensions:
            vr = cast("dict[str, Any]", ext.get("valueReference", {}) or {})
            ident = cast("dict[str, Any]", vr.get("identifier", {}) or {})
            v = str(ident.get("value", "") or "").strip()
            if v and looks_like_url(v):
                return v

        for ext in extensions:
            u = str(ext.get("url", "") or "").strip()
            if u and looks_like_url(u):
                return u

        return None


# TODO: Delete this but leave for now to make sure I'm calling right
# ---------------- example usage ----------------
if __name__ == "__main__":
    sds = SdsClient(
        api_key="any-value-works-in-sandbox",
        base_url=SdsClient.SANDBOX_URL,
    )

    result = sds.lookup_device_asid_and_endpoint(
        device_ods_code="YES",
        # Optionally override these:
        # service_interaction_id="urn:nhs:names:services:psis:REPC_IN150016UK05",
        # party_key="YES-0000806",
    )

    print(result)
