from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StubResponse:
    status_code: int
    headers: dict[str, str]
    json: dict[str, Any]


class PdsFhirApiStub:
    """
    Minimal in-memory stub for the PDS FHIR API, implementing only GET /Patient/{id}.

    Contract elements modelled from the provided OpenAPI:
        - Path: /Patient/{id}
        - id is the patient's NHS number (10 digits, must be valid)
        - X-Request-ID is mandatory and mirrored back in a response header
        - X-Correlation-ID is optional and mirrored back if supplied
        - ETag follows W/"<version>" and corresponds to Patient.meta.versionId

    See uploaded OpenAPI for details.
    """

    def __init__(self, strict_headers: bool = True) -> None:
        # strict_headers=True enforces X-Request-ID presence and UUID format.
        self.strict_headers = strict_headers
        # Internal store: nhs_number -> (patient_resource, version_id_int)
        self._patients: dict[str, tuple[dict[str, Any], int]] = {}

        # Seed a deterministic example matching the spec's id example.
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
                    }
                ],
                "gender": "female",
                "birthDate": "1970-01-01",
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
        """Add/replace a patient in the stub store."""

        try:
            nhsnum_match = re.fullmatch(r"(\d{10})", nhs_number)
        except TypeError as err:
            raise TypeError("NHS Number must be a string") from err

        if not nhsnum_match:
            raise ValueError("NHS Number must be exactly 10 digits")

        if not self._is_valid_nhs_number(nhs_number):
            raise ValueError("NHS Number is not valid")

        patient = dict(patient) if patient is not None else {}

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
        authorization: str | None = None,  # noqa F841 # Ignored in stub
        role_id: str | None = None,  # noqa F841 # Ignored in stub
        end_user_org_ods: str | None = None,  # noqa F841 # Ignored in stub
    ) -> StubResponse:
        """
        Implements GET /Patient/{id}.
        """
        headers_out: dict[str, str] = {}

        # Header handling (mirroring behavior).
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
        if request_id:
            headers_out["X-Request-Id"] = request_id
        if correlation_id:
            headers_out["X-Correlation-Id"] = correlation_id

        # Path parameter validation: 10 digits and valid NHS number.

        if not re.fullmatch(
            r"\d{10}", nhs_number or ""
        ) or not self._is_valid_nhs_number(nhs_number):
            return self._operation_outcome(
                status_code=400,
                headers=headers_out,
                spine_code="INVALID_RESOURCE_ID",
                display="Resource Id is invalid",
            )

        # Lookup.
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
        return StubResponse(status_code=200, headers=headers_out, json=patient)

    # ---------------------------
    # Internal helpers
    # ---------------------------

    @staticmethod
    def _now_fhir_instant() -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            uuid.UUID(value)
            return True
        except Exception:
            return False

    @staticmethod
    def _is_valid_nhs_number(nhs_number: str) -> bool:
        """
        NHS number check-digit validation (mod 11).
        Rejects cases where computed check digit is 10.
        """
        # TODO: The AI did this. Check it's correct but also do we need this validation
        # in the stub? In the mean time, just pass everything.
        return True
        # digits = [int(c) for c in nhs_number]
        # total = sum(digits[i] * (10 - i) for i in range(9))  # weights 10..2
        # remainder = total % 11
        # check = 11 - remainder
        # if check == 11:
        #     check = 0
        # if check == 10:
        #     return False
        # return digits[9] == check

    def _bad_request(
        self, message: str, *, request_id: str | None, correlation_id: str | None
    ) -> StubResponse:
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
    ) -> StubResponse:
        # Matches the example structure shown in the OpenAPI file.
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
        return StubResponse(status_code=status_code, headers=dict(headers), json=body)
