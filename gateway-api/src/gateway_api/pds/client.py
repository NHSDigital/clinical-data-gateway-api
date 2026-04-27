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

import logging
import os
import uuid

import requests
from fhir.r4 import Patient
from pydantic import ValidationError

from gateway_api.common.error import PdsRequestFailedError

# TODO [GPCAPIM-359]: Once stub servers/containers made for PDS, SDS and provider
#       we should remove the PDS_URL environment variable and just
#       use the stub client
STUB_PDS = os.environ["PDS_URL"].lower() == "stub"

if not STUB_PDS:
    from requests import get
else:
    from stubs.pds.stub import PdsFhirApiStub

    pds = PdsFhirApiStub()
    get = pds.get  # type: ignore

_logger = logging.getLogger(__name__)


class PdsClient:
    """
    Simple client for PDS FHIR R4 patient retrieval.

    The client currently supports one operation:

    * :meth:`search_patient_by_nhs_number` - calls ``GET /Patient/{nhs_number}``

    This method returns a :class:`Patient` instance when a patient can be
    extracted, otherwise  raise `PdsRequestFailedError` with a reason for the failure.

    **Usage example**::

        pds = PdsClient(
            auth_token="YOUR_ACCESS_TOKEN",
            base_url="https://sandbox.api.service.nhs.uk/personal-demographics/FHIR/R4",
        )

        result = pds.search_patient_by_nhs_number(9000000009)

        if result:
            print(result)
    """

    def __init__(
        self,
        auth_token: str,
        base_url: str,
        timeout: int = 10,
        ignore_dates: bool = False,
    ) -> None:
        self.auth_token = auth_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.ignore_dates = ignore_dates

        log_details = {
            "description": "Initialized PdsClient",
            "base_url": self.base_url,
        }
        _logger.info(log_details)

    def _build_headers(
        self,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """
        Build mandatory and optional headers for a PDS request.
        """
        headers = {
            "X-Request-ID": request_id or str(uuid.uuid4()),
            "Accept": "application/fhir+json",
            "Authorization": f"Bearer {self.auth_token}",
        }

        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id

        return headers

    def search_patient_by_nhs_number(
        self,
        nhs_number: str,
        request_id: str | None = None,
        correlation_id: str | None = None,
        timeout: int | None = None,
    ) -> Patient:
        """
        Retrieve a patient by NHS number.

        Calls ``GET /Patient/{nhs_number}``, which returns a single FHIR Patient
        resource on success, then builds and returns a single :class:`Patient`.
        """
        headers = self._build_headers(
            request_id=request_id,
            correlation_id=correlation_id,
        )

        url = f"{self.base_url}/Patient/{nhs_number}"

        log_details = {
            "description": "PDS request",
            "url": url,
        }
        _logger.info(log_details)
        # This normally calls requests.get, but if PDS_URL is set it uses the stub.
        response = get(
            url,
            headers=headers,
            params={},
            timeout=timeout or self.timeout,
        )
        log_details = {
            "description": "PDS response received",
            "status_code": str(response.status_code),
        }
        _logger.info(log_details)

        try:
            response.raise_for_status()
        except requests.HTTPError as err:
            raise PdsRequestFailedError(error_reason=err.response.reason) from err

        try:
            patient = Patient.model_validate(response.json())
        except ValidationError as err:
            first_error = err.errors()[0]
            raise PdsRequestFailedError(
                error_reason=str(first_error),
            ) from err

        return patient
