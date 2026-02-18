"""
PDS (Personal Demographics Service) FHIR R4 patient lookup client.

Contracts enforced by the helper functions:

* ``Patient.name[]`` records passed to :func:`find_current_name_record` must contain::

    record["period"]["start"]
    record["period"]["end"]

* ``Patient.generalPractitioner[]`` records passed to :func:`find_current_record` must
    contain::

    record["identifier"]["period"]["start"]
    record["identifier"]["period"]["end"]

If required keys are missing, a ``KeyError`` is raised intentionally. This is treated as
malformed upstream data (or malformed test fixtures) and should be corrected at source.
"""

import os
import uuid
from datetime import date, datetime, timezone
from typing import cast

import requests
from fhir import Bundle, BundleEntry, GeneralPractitioner, HumanName, Patient

from gateway_api.common.error import PdsRequestFailed
from gateway_api.pds.search_results import PdsSearchResults

# TODO: Once stub servers/containers made for PDS, SDS and provider
#       we should remove the STUB_PDS environment variable and just
#       use the stub client
STUB_PDS = os.environ.get("STUB_PDS", "false").lower() == "true"
if not STUB_PDS:
    post = requests.post
else:
    from stubs.pds.stub import PdsFhirApiStub

    pds = PdsFhirApiStub()
    post = pds.post  # type: ignore


class PdsClient:
    """
    Simple client for PDS FHIR R4 patient retrieval.

    The client currently supports one operation:

    * :meth:`search_patient_by_nhs_number` - calls ``GET /Patient/{nhs_number}``

    This method returns a :class:`PdsSearchResults` instance when a patient can be
    extracted, otherwise ``None``.

    **Usage example**::

        pds = PdsClient(
            auth_token="YOUR_ACCESS_TOKEN",
            base_url="https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4",
        )

        result = pds.search_patient_by_nhs_number(9000000009)

        if result:
            print(result)
    """

    # URLs for different PDS environments. Requires authentication to use live.
    SANDBOX_URL = "https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4"
    INT_URL = "https://int.api.service.nhs.uk/personal-demographics/FHIR/R4"
    PROD_URL = "https://api.service.nhs.uk/personal-demographics/FHIR/R4"

    def __init__(
        self,
        auth_token: str,
        base_url: str = SANDBOX_URL,
        timeout: int = 10,
        ignore_dates: bool = False,
    ) -> None:
        """
        Create a PDS client.

        :param auth_token: OAuth2 bearer token (without the ``"Bearer "`` prefix).
        :param base_url: Base URL for the PDS API (one of :attr:`SANDBOX_URL`,
            :attr:`INT_URL`, :attr:`PROD_URL`). Trailing slashes are stripped.
        :param timeout: Default timeout in seconds for HTTP calls.
        :param ignore_dates: If ``True`` just get the most recent name or GP record,
            ignoring the date ranges.
        """
        self.auth_token = auth_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.ignore_dates = ignore_dates

    def _build_headers(
        self,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """
        Build mandatory and optional headers for a PDS request.

        :param request_id: Optional ``X-Request-ID``. If not supplied a new UUID is
                            generated.
        :param correlation_id: Optional ``X-Correlation-ID`` for cross-system tracing.
        :return: Dictionary of HTTP headers for the outbound request.
        """
        headers = {
            "X-Request-ID": request_id or str(uuid.uuid4()),
            "Accept": "application/fhir+json",
            "Authorization": f"Bearer {self.auth_token}",
        }

        # Correlation ID is used to track the same request across multiple systems.
        # Can be safely omitted, mirrored back in response if included.
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    def search_patient_by_nhs_number(
        self,
        nhs_number: str,
        request_id: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> PdsSearchResults | None:
        """
        Retrieve a patient by NHS number.

        Calls ``GET /Patient/{nhs_number}``, which returns a single FHIR Patient
        resource on success, then extracts a single :class:`PdsSearchResults`.

        :param nhs_number: NHS number to search for.
        :param request_id: Optional request ID to reuse for retries; if not supplied a
            UUID is generated.
        :param correlation_id: Optional correlation ID for tracing.
        :param timeout: Optional per-call timeout in seconds. If not provided,
            :attr:`timeout` is used.
        :return: A :class:`PdsSearchResults` instance if a patient can be extracted,
            otherwise ``None``.
        """
        headers = self._build_headers(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        url = f"{self.base_url}/Patient/{nhs_number}"

        # This normally calls requests.get, but if STUB_PDS is set it uses the stub.
        response = post(
            url,  # TODO: URL points to sandbox env even when STUB_PDS
            #       is true, should we change this to point to the stub instead?
            headers=headers,
            params={},
            timeout=timeout or self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise PdsRequestFailed(error_reason=err.response.reason) from err

        body = response.json()
        return self._extract_single_search_result(body)

    # --------------- internal helpers for result extraction -----------------

    def _get_gp_ods_code(
        self, general_practitioners: list[GeneralPractitioner]
    ) -> str | None:
        """
        Extract the current GP ODS code from ``Patient.generalPractitioner``.

        This function implements the business rule:

        * If the list is empty, return ``None``.
        * If the list is non-empty and no record is current, return ``None``.
        * If exactly one record is current, return its ``identifier.value``.

        In future this may change to return the most recent record if none is current.

        :param general_practitioners: List of ``generalPractitioner`` records from a
            Patient resource.
        :return: ODS code string if a current record exists, otherwise ``None``.
        :raises KeyError: If a record is missing required ``identifier.period`` fields.
        """
        if len(general_practitioners) == 0:
            return None

        gp = self.find_current_gp(general_practitioners)
        if gp is None:
            return None

        ods_code = gp["identifier"]["value"]

        return None if ods_code == "None" else ods_code

    def _extract_single_search_result(
        self, body: Patient | Bundle
    ) -> PdsSearchResults | None:
        """
        Extract a single :class:`PdsSearchResults` from a Patient response.

        This helper accepts either:
        * a single FHIR Patient resource (as returned by ``GET /Patient/{id}``), or
        * a FHIR Bundle containing Patient entries (as typically returned by searches).

        For Bundle inputs, the code assumes either zero matches (empty entry list) or a
        single match; if multiple entries are present, the first entry is used.
        :param body: Parsed JSON body containing either a Patient resource or a Bundle
            whose first entry contains a Patient resource under ``resource``.
        :return: A populated :class:`PdsSearchResults` if extraction succeeds, otherwise
            ``None``.
        """
        # Accept either:
        # 1) Patient (GET /Patient/{id})
        # 2) Bundle with Patient in entry[0].resource (search endpoints)
        if str(body.get("resourceType", "")) == "Patient":
            patient = cast("Patient", body)
        else:
            entries = cast("list[BundleEntry]", body.get("entry", []))
            if not entries:
                raise RuntimeError("PDS response contains no patient entries")

            # Use the first patient entry. Search by NHS number is unique. Search by
            # demographics for an application is allowed to return max one entry from
            # PDS. Search by a human can return more, but presumably we count as an
            # application.
            # See MaxResults parameter in the PDS OpenAPI spec.
            entry = entries[0]
            patient = cast("Patient", entry.get("resource", {}))

        nhs_number = str(patient.get("id", "")).strip()
        if not nhs_number:
            raise RuntimeError("PDS patient resource missing NHS number")

        current_name = self.find_current_name_record(patient["name"])

        if current_name is not None:
            given_names = " ".join(current_name.get("given", [])).strip()
            family_name = current_name.get("family", "")
        else:
            given_names = ""
            family_name = ""

        # Extract GP ODS code if a current GP record exists.
        gp_ods_code = self._get_gp_ods_code(patient.get("generalPractitioner", []))

        return PdsSearchResults(
            given_names=given_names,
            family_name=family_name,
            nhs_number=nhs_number,
            gp_ods_code=gp_ods_code,
        )

    def find_current_gp(
        self,
        gerneral_practitioners: list[GeneralPractitioner],
        today: date | None = None,
    ) -> GeneralPractitioner | None:
        """
        Select the current record from a ``generalPractitioner`` list.

        A record is "current" if its ``identifier.period`` covers ``today`` (inclusive):

        ``start <= today <= end``

        Or else if self.ignore_dates is True, the last record in the list is returned.

        The list may be in any of the following states:

        * empty
        * contains one or more records, none current
        * contains one or more records, exactly one current

        :param records: List of ``generalPractitioner`` records.
        :param today: Optional override date, intended for deterministic tests.
            If not supplied, the current UTC date is used.
        :return: The first record whose ``identifier.period`` covers ``today``, or
            ``None`` if no record is current.
        :raises KeyError: If required keys are missing for a record being evaluated.
        :raises ValueError: If ``start`` or ``end`` are not valid ISO date strings.
        """
        if today is None:
            today = datetime.now(timezone.utc).date()

        if self.ignore_dates:
            if len(gerneral_practitioners) > 0:
                return gerneral_practitioners[-1]
            else:
                return None

        for record in gerneral_practitioners:
            period = record["identifier"]["period"]  # TODO: spell check lint
            start = date.fromisoformat(period["start"])
            end = date.fromisoformat(period["end"])
            if start <= today <= end:
                return record

        return None

    def find_current_name_record(
        self, names: list[HumanName], today: date | None = None
    ) -> HumanName | None:
        """
        Select the current record from a ``Patient.name`` list.

        A record is "current" if its ``period`` covers ``today`` (inclusive):

        ``start <= today <= end``

        Or else if self.ignore_dates is True, the last record in the list is returned.

        :param records: List of ``Patient.name`` records.
        :param today: Optional override date, intended for deterministic tests.
            If not supplied, the current UTC date is used.
        :return: The first name record whose ``period`` covers ``today``, or ``None`` if
            no record is current.
        :raises KeyError: If required keys (``period.start`` / ``period.end``) are
            missing.
        :raises ValueError: If ``start`` or ``end`` are not valid ISO date strings.
        """
        if today is None:
            today = datetime.now(timezone.utc).date()

        if self.ignore_dates:
            if len(names) > 0:
                return names[-1]
            else:
                return None

        for name in names:
            period = cast("dict[str, str]", name["period"])
            start = date.fromisoformat(period["start"])
            end = date.fromisoformat(period["end"])
            if start <= today <= end:
                return name

        return None
