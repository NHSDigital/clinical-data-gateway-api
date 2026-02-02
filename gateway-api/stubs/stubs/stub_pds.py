"""
In-memory PDS FHIR R4 API stub.

The stub does **not** implement the full PDS API surface, nor full FHIR validation.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from requests import Response
from requests.structures import CaseInsensitiveDict


def _create_response(
    status_code: int,
    headers: dict[str, str],
    json_data: dict[str, Any],
) -> Response:
    """
    Create a :class:`requests.Response` object for the stub.

    :param status_code: HTTP status code.
    :param headers: Response headers dictionary.
    :param json_data: JSON body data.
    :return: A :class:`requests.Response` instance.
    """
    response = Response()
    response.status_code = status_code
    response.headers = CaseInsensitiveDict(headers)
    response._content = json.dumps(json_data).encode("utf-8")  # noqa: SLF001
    response.encoding = "utf-8"
    return response


class PdsFhirApiStub:
    """
    Minimal in-memory stub for the PDS FHIR API, implementing only ``GET /Patient/{id}``

    Contract elements modelled from the PDS OpenAPI spec:

    * ``/Patient/{id}`` where ``id`` is the patient's NHS number (10 digits)
    * ``X-Request-ID`` is mandatory (in strict mode) and echoed back as ``X-Request-Id``
    * ``X-Correlation-ID`` is optional and echoed back as ``X-Correlation-Id``
        if supplied
    * ``ETag`` follows ``W/"<version>"`` and corresponds to ``Patient.meta.versionId``

    See:
        https://github.com/NHSDigital/personal-demographics-service-api/blob/master/specification/personal-demographics.yaml
    """

    def __init__(self, strict_headers: bool = True) -> None:
        """
        Create a new stub instance.

        :param strict_headers: If ``True``, enforce presence and UUID format of
            ``X-Request-ID``. If ``False``, header validation is relaxed.
        """
        self.strict_headers = strict_headers

        # Internal store: nhs_number -> (patient_resource, version_id_int)
        self._patients: dict[str, tuple[dict[str, Any], int]] = {}

        # Seed a deterministic example matching the spec's id example.
        # Tests may overwrite this record via upsert_patient.
        self.upsert_patient(
            nhs_number="9000000009",
            patient={
                "resourceType": "Patient",
                "id": "9000000009",
                "meta": {
                    "versionId": "1",
                    "lastUpdated": "2020-01-01T00:00:00Z",
                },
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9000000009",
                    }
                ],
                "name": [
                    {
                        "use": "official",
                        "family": "Smith",
                        "given": ["Jane"],
                        "period": {"start": "1900-01-01", "end": "9999-12-31"},
                    }
                ],
                "gender": "female",
                "birthDate": "1970-01-01",
            },
            version_id=1,
        )

        self.upsert_patient(
            nhs_number="9999999999",
            patient={
                "resourceType": "Patient",
                "id": "9999999999",
                "meta": {
                    "versionId": "1",
                    "lastUpdated": "2020-01-01T00:00:00Z",
                },
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9999999999",
                    }
                ],
                "name": [
                    {
                        "use": "official",
                        "family": "Jones",
                        "given": ["Alice"],
                        "period": {"start": "1900-01-01", "end": "9999-12-31"},
                    }
                ],
                "gender": "female",
                "birthDate": "1980-01-01",
            },
            version_id=1,
        )

    # ---------------------------
    # Public API for tests
    # ---------------------------

    def upsert_patient(
        self,
        nhs_number: str,
        patient: dict[str, Any] | None = None,
        version_id: int = 1,
    ) -> None:
        """
        Insert or replace a patient record in the stub store.

        :param nhs_number: NHS number as a 10-digit string.
        :param patient: Patient resource dictionary. If ``None``, an empty Patient dict
            is created and populated with required keys.
        :param version_id: Version integer recorded into
            ``patient["meta"]["versionId"]`` and used to generate the ETag on retrieval.
        :return: ``None``.
        :raises TypeError: If ``nhs_number`` is not a string.
        :raises ValueError: If ``nhs_number`` is not 10 digits or fails validation.
        """
        try:
            nhsnum_match = re.fullmatch(r"(\d{10})", nhs_number)
        except TypeError as err:
            raise TypeError("NHS Number must be a string") from err

        if not nhsnum_match:
            raise ValueError("NHS Number must be exactly 10 digits")

        if not self._is_valid_nhs_number(nhs_number):
            raise ValueError("NHS Number is not valid")

        if patient is None:
            patient = {}

        patient.setdefault("resourceType", "Patient")
        patient["id"] = nhs_number
        patient.setdefault("meta", {})
        patient["meta"]["versionId"] = str(version_id)
        patient["meta"].setdefault("lastUpdated", self._now_fhir_instant())

        self._patients[nhs_number] = (patient, version_id)

    def get_patient(
        self,
        nhs_number: str,
        request_id: str | None = None,
        correlation_id: str | None = None,
        authorization: str | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        role_id: str | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        end_user_org_ods: str | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
    ) -> Response:
        """
        Implements ``GET /Patient/{id}``.

        :param nhs_number: The NHS number path parameter.
        :param request_id: The ``X-Request-ID`` header value. Required
            (and must be UUID) when ``strict_headers=True``.
        :param correlation_id: Optional ``X-Correlation-ID`` header value.
        :param authorization: Authorization header (ignored by the stub).
        :param role_id: Role header (ignored by the stub).
        :param end_user_org_ods: End-user ODS header (ignored by the stub).
        :return: A :class:`requests.Response` representing either:
            * ``200`` with Patient JSON
            * ``404`` with OperationOutcome JSON
            * ``400`` with OperationOutcome JSON (validation failures)
        """
        headers_out: dict[str, str] = {}

        # Header validation mirrors key behaviour enforced by the real service.
        if self.strict_headers:
            if not request_id:
                return self._bad_request(
                    "Missing X-Request-ID",
                    request_id=request_id,
                    correlation_id=correlation_id,
                )
            if not self._is_uuid(request_id):
                return self._bad_request(
                    "Invalid X-Request-ID (must be a UUID)",
                    request_id=request_id,
                    correlation_id=correlation_id,
                )

        # Echo trace headers back (note casing).
        if request_id:
            headers_out["X-Request-Id"] = request_id
        if correlation_id:
            headers_out["X-Correlation-Id"] = correlation_id

        # Path parameter validation: must be 10 digits and pass NHS-number validation.
        if not re.fullmatch(
            r"\d{10}", nhs_number or ""
        ) or not self._is_valid_nhs_number(nhs_number):
            return self._operation_outcome(
                status_code=400,
                headers=headers_out,
                spine_code="INVALID_RESOURCE_ID",
                display="Resource Id is invalid",
            )

        # Lookup: not present => 404 OperationOutcome.
        if nhs_number not in self._patients:
            return self._operation_outcome(
                status_code=404,
                headers=headers_out,
                spine_code="RESOURCE_NOT_FOUND",
                display="Patient not found",
            )

        patient, version_id = self._patients[nhs_number]

        # ETag mirrors the "W/\"<n>\"" shape and aligns to meta.versionId.
        headers_out["ETag"] = f'W/"{version_id}"'
        return _create_response(status_code=200, headers=headers_out, json_data=patient)

    def get(
        self,
        url: str,
        headers: dict[str, Any] | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        params: dict[str, Any] | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        timeout: int | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
    ) -> Response:
        nhs_number = url.split("/")[-1]
        return self.get_patient(nhs_number)

    # ---------------------------
    # Internal helpers
    # ---------------------------

    @staticmethod
    def _now_fhir_instant() -> str:
        """
        Generate a FHIR instant timestamp in UTC with seconds precision.

        :return: Timestamp string in the format ``YYYY-MM-DDTHH:MM:SSZ``.
        """
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _is_uuid(value: str) -> bool:
        """
        Determine whether a string can be parsed as a UUID.

        :param value: Candidate value.
        :return: ``True`` if the value parses as a UUID, otherwise ``False``.
        """
        try:
            uuid.UUID(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_valid_nhs_number(
        nhs_number: str,  # NOQA: ARG004 We're just passing everything
    ) -> bool:
        """
        Validate an NHS number. We don't actually care if NHS numbers are valid in the
        stub for now, so just returns True.

        If you do decide that you want to validate them in future, use the validator
        in common.common.validate_nhs_number.
        """
        return True

    def _bad_request(
        self, message: str, *, request_id: str | None, correlation_id: str | None
    ) -> Response:
        """
        Build a 400 OperationOutcome response.

        :param message: Human-readable error message.
        :param request_id: Optional request ID to echo back.
        :param correlation_id: Optional correlation ID to echo back.
        :return: A 400 :class:`requests.Response` containing an OperationOutcome.
        """
        headers: dict[str, str] = {}
        if request_id:
            headers["X-Request-Id"] = request_id
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id

        return self._operation_outcome(
            status_code=400,
            headers=headers,
            spine_code="INVALID_REQUEST",
            display=message,
        )

    @staticmethod
    def _operation_outcome(
        *, status_code: int, headers: dict[str, str], spine_code: str, display: str
    ) -> Response:
        """
        Construct an OperationOutcome response body.

        :param status_code: HTTP-like status code.
        :param headers: Response headers.
        :param spine_code: Spine error/warning code.
        :param display: Human-readable display message.
        :return: A :class:`requests.Response` containing an OperationOutcome JSON body.
        """
        body = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "value",
                    "details": {
                        "coding": [
                            {
                                "system": "https://fhir.nhs.uk/R4/CodeSystem/Spine-ErrorOrWarningCode",
                                "version": "1",
                                "code": spine_code,
                                "display": display,
                            }
                        ]
                    },
                }
            ],
        }
        return _create_response(
            status_code=status_code, headers=dict(headers), json_data=body
        )
