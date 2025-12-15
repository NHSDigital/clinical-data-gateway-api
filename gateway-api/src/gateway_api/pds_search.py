import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import TypeAlias, cast

import requests

Result: TypeAlias = str | dict[str, "Result"] | list["Result"]


@dataclass
class SearchResults:
    """
    Represents a single patient search result with only the fields requested:
    - Given name(s)
    - Family name
    - NHS Number
    - Current general practitioner ODS code
    """

    given_names: str
    family_name: str
    nhs_number: str
    gp_ods_code: str | None


class PdsSearch:
    """
    Simple client for PDS FHIR R4 patient search (GET /Patient).

    Usage:

        pds = PdsSearch(
            auth_token="YOUR_ACCESS_TOKEN",
            end_user_org_ods="A12345",
            base_url="https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4",
        )

        result = pds.search_patient(
            family="Smith",
            given="John",
            gender="male",
            date_of_birth="1980-05-12",
            postcode="SW1A1AA",
        )

        if result:
            print(result)
    """

    # Defaults – adjust as needed
    SANDBOX_URL = "https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4"
    INT_URL = "https://int.api.service.nhs.uk/personal-demographics/FHIR/R4"
    PROD_URL = "https://api.service.nhs.uk/personal-demographics/FHIR/R4"

    def __init__(
        self,
        auth_token: str,
        end_user_org_ods: str,
        base_url: str = SANDBOX_URL,
        *,
        nhsd_session_urid: str | None = None,
        timeout: int = 10,
    ) -> None:
        """
        :param auth_token: OAuth2 bearer token (without 'Bearer ' prefix)
        :param end_user_org_ods: NHSD End User Organisation ODS code
        :param base_url: Base URL for the PDS API (one of SANDBOX_URL / INT_URL /
        PROD_URL)
        :param nhsd_session_urid: Optional NHSD-Session-URID (for healthcare worker
        access)
        :param timeout: Default timeout in seconds for HTTP calls
        """
        self.auth_token = auth_token
        self.end_user_org_ods = end_user_org_ods
        self.base_url = base_url.rstrip("/")
        self.nhsd_session_urid = nhsd_session_urid
        self.timeout = timeout

    def _build_headers(
        self,
        *,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """
        Build mandatory and optional headers for a PDS request.
        """
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "X-Request-ID": request_id or str(uuid.uuid4()),
            "NHSD-End-User-Organisation-ODS": self.end_user_org_ods,
            "Accept": "application/fhir+json",
        }

        if self.nhsd_session_urid:
            headers["NHSD-Session-URID"] = self.nhsd_session_urid

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    def search_patient(
        self,
        *,
        family: str,
        given: str,
        gender: str,
        date_of_birth: str,
        postcode: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        # These options are exposed by the PDS API but we don't need them,
        # at least for now
        # fuzzy_match: bool = False,
        # exact_match: bool = False,
        # history: bool = False,
        # max_results: Optional[int] = None,
        request_id: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> SearchResults | None:
        """
        Perform a patient search using GET /Patient on the PDS FHIR R4 API.

        Assumes that the search will return a single matching patient.

        Required:
            family          Patient family name (surname)
            given           Patient given name
            gender          'male' | 'female' | 'other' | 'unknown'
            date_of_birth   'YYYY-MM-DD' (exact match, wrapped as eqYYYY-MM-DD)

        Optional:
            postcode        Patient postcode (address-postalcode)
            email           Patient email address
            phone           Patient phone number
            fuzzy_match     If True, sets _fuzzy-match=true
            exact_match     If True, sets _exact-match=true
            history         If True, sets _history=true
            max_results     Integer 1–50
            request_id      Override X-Request-ID (otherwise auto-generated UUID)
            correlation_id  Optional X-Correlation-ID
            timeout         Per-call timeout (defaults to client-level timeout)

        Returns:
            A single SearchResults instance if a patient is found, else None.
        """

        headers = self._build_headers(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        params: dict[str, str] = {
            "family": family,
            "given": given,
            "gender": gender,
            # Exact DOB match
            "birthdate": f"eq{date_of_birth}",
        }

        if postcode:
            # Use address-postalcode (address-postcode is deprecated)
            params["address-postalcode"] = postcode

        if email:
            params["email"] = email

        if phone:
            params["phone"] = phone

        # # Optional flags
        # if fuzzy_match:
        #     params["_fuzzy-match"] = "true"
        # if exact_match:
        #     params["_exact-match"] = "true"
        # if history:
        #     params["_history"] = "true"
        # if max_results is not None:
        #     params["_max-results"] = max_results

        url = f"{self.base_url}/Patient"

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout or self.timeout,
        )

        try:
            response.raise_for_status()
        except requests.HTTPError:
            # TODO: This should log, or something
            return None

        bundle = response.json()
        return self._extract_single_search_result(bundle)

    # --------------- internal helpers for result extraction -----------------

    @staticmethod
    def _get_gp_ods_code(general_practitioners: list[dict[str, Result]]) -> str | None:
        """
        Extract the current general practitioner ODS code from
        Patient.generalPractitioner[].identifier.value, if present.
        """
        if len(general_practitioners) == 0:
            return None

        gp = find_current_record(general_practitioners)
        if gp is None:
            return None

        identifier = cast("dict[str, Result]", gp.get("identifier", {}))
        ods_code = str(identifier.get("value", None))

        return ods_code

    def _extract_single_search_result(
        self, bundle: dict[str, Result]
    ) -> SearchResults | None:
        """
        Convert a FHIR Bundle from /Patient search into a single SearchResults
        object by using the first entry. Returns None if there are no entries.
        """
        entries: list[dict[str, Result]] = cast(
            "list[dict[str, Result]]", bundle.get("entry", [])
        )  # entries["entry"] is definitely a list
        if not entries:
            return None

        # Search can return multiple patients, except that for APIs it can only
        # return one, so this is fine
        entry = entries[0]
        patient = cast("dict[str, Result]", entry.get("resource", {}))

        nhs_number = str(patient.get("id", "")).strip()

        # Pretty sure NHS number has to be there
        if not nhs_number:
            return None

        names = cast("list[dict[str, Result]]", patient.get("name", []))
        name_obj = find_current_record(names)

        if name_obj is None:
            return None

        given_names_list = cast("list[str]", name_obj.get("given", []))
        family_name = str(name_obj.get("family", "")) or ""

        given_names_str = " ".join(given_names_list).strip()

        # TODO: What happens if the patient isn't registered with a GP so this is empty?
        #  Probably not for Alpha
        gp_list = cast(
            "list[dict[str, Result]]", patient.get("generalPractitioner", [])
        )
        gp_ods_code = self._get_gp_ods_code(gp_list)

        return SearchResults(
            given_names=given_names_str,
            family_name=family_name,
            nhs_number=nhs_number,
            gp_ods_code=gp_ods_code,
        )


def find_current_record(
    records: list[dict[str, Result]], today: date | None = None
) -> dict[str, Result] | None:
    """
    records: list of dicts, each with period.start and period.end (ISO date strings).
    today: optional date override (for testing); defaults to today's date.
    Returns: the first dict whose period covers 'today', or None if no match.
    """
    if today is None:
        # TODO: Do we need to do something about UTC here? Do we need to use local time?
        #  Don't worry for Alpha
        today = datetime.now(timezone.utc).date()

    for record in records:
        periods = cast("dict[str, str]", record["period"])
        start_str = periods["start"]
        end_str = periods["end"]

        # Parse ISO dates
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)

        # Inclusive range check
        if start <= today <= end:
            return record

    return None
