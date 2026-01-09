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

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import cast

import requests

# Recursive JSON-like structure typing used for parsed FHIR bodies.
type ResultStructure = str | dict[str, "ResultStructure"] | list["ResultStructure"]
type ResultStructureDict = dict[str, ResultStructure]
type ResultList = list[ResultStructureDict]


class ExternalServiceError(Exception):
    """
    Raised when the downstream PDS request fails.

    This module catches :class:`requests.HTTPError` thrown by
    ``response.raise_for_status()`` and re-raises it as ``ExternalServiceError`` so
    callers are not coupled to ``requests`` exception types.
    """


@dataclass
class SearchResults:
    """
    A single extracted patient record.

    Only a small subset of the PDS Patient fields are currently required by this
    gateway. More will be added in later phases.

    :param given_names: Given names from the *current* ``Patient.name`` record,
        concatenated with spaces.
    :param family_name: Family name from the *current* ``Patient.name`` record.
    :param nhs_number: NHS number (``Patient.id``).
    :param gp_ods_code: The ODS code of the *current* GP, extracted from
        ``Patient.generalPractitioner[].identifier.value`` if a current GP record exists
        otherwise ``None``.
    """

    given_names: str
    family_name: str
    nhs_number: str
    gp_ods_code: str | None


class PdsClient:
    """
    Simple client for PDS FHIR R4 patient retrieval.

    The client currently supports one operation:

    * :meth:`search_patient_by_nhs_number` - calls ``GET /Patient/{nhs_number}``

    There is another operation implemented for searching by demographics:

    * :meth:`search_patient_by_details` - calls ``GET /Patient`` with query parameters

    ...but this is currently not fully tested. Its implementation may be finalised
    in a later phase if it is required.

    Both methods return a :class:`SearchResults` instance when a patient can be
    extracted, otherwise ``None``.

    **Usage example**::

        pds = PdsClient(
            auth_token="YOUR_ACCESS_TOKEN",
            end_user_org_ods="A12345",
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
        end_user_org_ods: str,
        base_url: str = SANDBOX_URL,
        nhsd_session_urid: str | None = None,
        timeout: int = 10,
    ) -> None:
        """
        Create a PDS client.

        :param auth_token: OAuth2 bearer token (without the ``"Bearer "`` prefix).
        :param end_user_org_ods: NHSD End User Organisation ODS code.
        :param base_url: Base URL for the PDS API (one of :attr:`SANDBOX_URL`,
            :attr:`INT_URL`, :attr:`PROD_URL`). Trailing slashes are stripped.
        :param nhsd_session_urid: Optional ``NHSD-Session-URID`` header value.
        :param timeout: Default timeout in seconds for HTTP calls.
        """
        self.auth_token = auth_token
        self.end_user_org_ods = end_user_org_ods
        self.base_url = base_url.rstrip("/")
        self.nhsd_session_urid = nhsd_session_urid
        self.timeout = timeout

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
            "Authorization": f"Bearer {self.auth_token}",
            "X-Request-ID": request_id or str(uuid.uuid4()),
            "NHSD-End-User-Organisation-ODS": self.end_user_org_ods,
            "Accept": "application/fhir+json",
        }

        # NHSD-Session-URID is required in some flows; include only if configured.
        if self.nhsd_session_urid:
            headers["NHSD-Session-URID"] = self.nhsd_session_urid

        # Correlation ID is used to track the same request across multiple systems.
        # Can be safely omitted, mirrored back in response if included.
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    def search_patient_by_nhs_number(
        self,
        nhs_number: int,
        request_id: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> SearchResults | None:
        """
        Retrieve a patient by NHS number.

        Calls ``GET /Patient/{nhs_number}``, which returns a single FHIR Patient
        resource on success, then extracts a single :class:`SearchResults`.

        :param nhs_number: NHS number to search for.
        :param request_id: Optional request ID to reuse for retries; if not supplied a
            UUID is generated.
        :param correlation_id: Optional correlation ID for tracing.
        :param timeout: Optional per-call timeout in seconds. If not provided,
            :attr:`timeout` is used.
        :return: A :class:`SearchResults` instance if a patient can be extracted,
            otherwise ``None``.
        :raises ExternalServiceError: If the HTTP request returns an error status and
            ``raise_for_status()`` raises :class:`requests.HTTPError`.
        """
        headers = self._build_headers(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        url = f"{self.base_url}/Patient/{nhs_number}"

        response = requests.get(
            url,
            headers=headers,
            params={},
            timeout=timeout or self.timeout,
        )

        try:
            # In production, failures surface here (4xx/5xx -> HTTPError).
            response.raise_for_status()
        except requests.HTTPError as err:
            raise ExternalServiceError("PDS request failed") from err

        body = response.json()
        return self._extract_single_search_result(body)

    # --------------- internal helpers for result extraction -----------------

    @staticmethod
    def _get_gp_ods_code(general_practitioners: ResultList) -> str | None:
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

        gp = find_current_gp(general_practitioners)
        if gp is None:
            return None

        identifier = cast("ResultStructureDict", gp.get("identifier", {}))
        ods_code = str(identifier.get("value", None))

        # Avoid returning the literal string "None" if identifier.value is absent.
        return None if ods_code == "None" else ods_code

    def _extract_single_search_result(
        self, body: ResultStructureDict
    ) -> SearchResults | None:
        """
        Extract a single :class:`SearchResults` from a Patient response.

        This helper accepts either:
        * a single FHIR Patient resource (as returned by ``GET /Patient/{id}``), or
        * a FHIR Bundle containing Patient entries (as typically returned by searches).

        For Bundle inputs, the code assumes either zero matches (empty entry list) or a
        single match; if multiple entries are present, the first entry is used.
        :param body: Parsed JSON body containing either a Patient resource or a Bundle
            whose first entry contains a Patient resource under ``resource``.
        :return: A populated :class:`SearchResults` if extraction succeeds, otherwise
            ``None``.
        """
        # Accept either:
        # 1) Patient (GET /Patient/{id})
        # 2) Bundle with Patient in entry[0].resource (search endpoints)
        if str(body.get("resourceType", "")) == "Patient":
            patient = body
        else:
            entries: ResultList = cast("ResultList", body.get("entry", []))
            if not entries:
                raise RuntimeError("PDS response contains no patient entries")

            # Use the first patient entry. Search by NHS number is unique. Search by
            # demographics for an application is allowed to return max one entry from
            # PDS. Search by a human can return more, but presumably we count as an
            # application.
            # See MaxResults parameter in the PDS OpenAPI spec.
            entry = entries[0]
            patient = cast("ResultStructureDict", entry.get("resource", {}))

        nhs_number = str(patient.get("id", "")).strip()
        if not nhs_number:
            raise RuntimeError("PDS patient resource missing NHS number")

        # Select current name record and extract names.
        names = cast("ResultList", patient.get("name", []))
        current_name = find_current_name_record(names)
        if current_name is None:
            raise RuntimeError("PDS patient has no current name record")

        given_names_list = cast("list[str]", current_name.get("given", []))
        family_name = str(current_name.get("family", "")) or ""
        given_names_str = " ".join(given_names_list).strip()

        # Extract GP ODS code if a current GP record exists.
        gp_list = cast("ResultList", patient.get("generalPractitioner", []))
        gp_ods_code = self._get_gp_ods_code(gp_list)

        return SearchResults(
            given_names=given_names_str,
            family_name=family_name,
            nhs_number=nhs_number,
            gp_ods_code=gp_ods_code,
        )


def find_current_gp(
    records: ResultList, today: date | None = None
) -> ResultStructureDict | None:
    """
    Select the current record from a ``generalPractitioner`` list.

    A record is "current" if its ``identifier.period`` covers ``today`` (inclusive):

    ``start <= today <= end``

    The list may be in any of the following states:

    * empty
    * contains one or more records, none current
    * contains one or more records, exactly one current

    :param records: List of ``generalPractitioner`` records.
    :param today: Optional override date, intended for deterministic tests.
        If not supplied, the current UTC date is used.
    :return: The first record whose ``identifier.period`` covers ``today``, or ``None``
        if no record is current.
    :raises KeyError: If required keys are missing for a record being evaluated.
    :raises ValueError: If ``start`` or ``end`` are not valid ISO date strings.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    for record in records:
        identifier = cast("ResultStructureDict", record["identifier"])
        periods = cast("dict[str, str]", identifier["period"])
        start_str = periods["start"]
        end_str = periods["end"]

        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)

        if start <= today <= end:
            return record

    return None


def find_current_name_record(
    records: ResultList, today: date | None = None
) -> ResultStructureDict | None:
    """
    Select the current record from a ``Patient.name`` list.

    A record is "current" if its ``period`` covers ``today`` (inclusive):

    ``start <= today <= end``

    :param records: List of ``Patient.name`` records.
    :param today: Optional override date, intended for deterministic tests.
        If not supplied, the current UTC date is used.
    :return: The first name record whose ``period`` covers ``today``, or ``None`` if no
        record is current.
    :raises KeyError: If required keys (``period.start`` / ``period.end``) are missing.
    :raises ValueError: If ``start`` or ``end`` are not valid ISO date strings.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    for record in records:
        periods = cast("dict[str, str]", record["period"])
        start_str = periods["start"]
        end_str = periods["end"]

        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)

        if start <= today <= end:
            return record

    return None
