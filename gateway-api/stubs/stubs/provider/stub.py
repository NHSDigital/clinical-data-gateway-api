"""
Minimal in-memory stub for a Provider GP System FHIR API,
implementing only accessRecordStructured to read basic
demographic data for a single patient.

Contract elements for direct provider calls are inferred from
GPConnect documentation:
https://developer.nhs.uk/apis/gpconnect/accessrecord_structured_development_retrieve_patient_record.html
    - Method: POST
    - fhir_base: /FHIR/STU3
    - resource: /Patient
    - fhir_operation: $gpc.getstructuredrecord

Headers:
    Ssp-TraceID: Consumer's Trace ID (a GUID or UUID)
    Ssp-From: Consumer's ASID
    Ssp-To: Provider's ASID
    Ssp-InteractionID:
        urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1

Request Body JSON (FHIR STU3 Parameters resource with patient NHS number.
"""

import json
from typing import Any

from requests import Response
from src.gateway_api.clinical_jwt import JWT, JWTValidator
from src.gateway_api.common.error import JWTValidationError
from src.gateway_api.get_structured_record import (
    ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
)

from stubs.base_stub import PostStub, StubBase
from stubs.data.bundles import Bundles


class GpProviderStub(StubBase, PostStub):
    """
    A minimal in-memory stub for a Provider GP System FHIR API,
    implementing only accessRecordStructured to read basic
    demographic data for a single patient.

    Seeded with an example
    FHIR/STU3 Patient resource with only administrative data based on Example 2
    # https://simplifier.net/guide/gp-connect-access-record-structured/Home/Examples/Allergy-examples?version=1.6.2
    """

    def __init__(self) -> None:
        self._post_url: str = ""
        self._post_headers: dict[str, str] = {}
        self._post_data: str = ""
        self._post_timeout: int | None = None

    @property
    def post_url(self) -> str:
        return self._post_url

    @property
    def post_headers(self) -> dict[str, str]:
        return self._post_headers

    @property
    def post_data(self) -> str:
        return self._post_data

    @property
    def post_timeout(self) -> int | None:
        return self._post_timeout

    def _validate_headers(self, headers: dict[str, Any]) -> Response | None:
        """
        Validate required headers for GPConnect FHIR API request.

        Returns:
            Response: Error response if validation fails, None if valid.
        """
        required_headers = {
            "Ssp-TraceID",
            "Ssp-From",
            "Ssp-To",
            "Ssp-InteractionID",
            "Content-Type",
            "Authorization",
        }

        # Check for missing headers
        missing_headers = []
        for header in required_headers:
            if header not in headers or not headers[header]:
                missing_headers.append(header)

        if missing_headers:
            error_msg = ", ".join(f"{h} is required" for h in missing_headers)
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": error_msg,
                        }
                    ],
                },
            )

        # Validate Content-Type
        content_type = headers.get("Content-Type", "")
        if "application/fhir+json" not in content_type:
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": "Content-Type must be application/fhir+json",
                        }
                    ],
                },
            )

        # Validate Ssp-InteractionID
        interaction_id = headers.get("Ssp-InteractionID", "")
        if interaction_id != ACCESS_RECORD_STRUCTURED_INTERACTION_ID:
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": (
                                f"Invalid Ssp-InteractionID: expected "
                                f"{ACCESS_RECORD_STRUCTURED_INTERACTION_ID}"
                            ),
                        }
                    ],
                },
            )

        # Validate Authorization header format and JWT
        auth_header = headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": (
                                "Authorization header must start with 'Bearer '"
                            ),
                        }
                    ],
                },
            )

        # Extract and validate JWT
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            jwt_obj = JWT.decode(token)
        except Exception as e:
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": f"Invalid JWT: {e!s}",
                        }
                    ],
                },
            )

        # Validate JWT structure and contents
        try:
            JWTValidator.validate(jwt_obj)
        except JWTValidationError as e:
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": str(e),
                        }
                    ],
                },
            )

        return None

    def access_record_structured(
        self,
        trace_id: str,
        body: str,
        headers: dict[str, Any],
    ) -> Response:
        """
        Simulate accessRecordStructured operation of GPConnect FHIR API.

        returns:
            Response: The stub patient bundle wrapped in a Response object.
        """
        # Validate that all required parameters are provided
        missing_params: list[str] = []
        if not body:
            missing_params.append("body")
        if not headers:
            missing_params.append("headers")

        if missing_params:
            error_msg = ", ".join(f"{param} is required" for param in missing_params)
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": error_msg,
                        }
                    ],
                },
            )

        # Validate headers
        validation_error = self._validate_headers(headers)
        if validation_error is not None:
            return validation_error

        if trace_id == "invalid for test":
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": "Invalid for testing",
                        }
                    ],
                },
            )

        try:
            nhs_number = json.loads(body)["parameter"][0]["valueIdentifier"]["value"]
        except (json.JSONDecodeError, KeyError, IndexError):
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": "Malformed request body",
                        }
                    ],
                },
            )

        if nhs_number == "9999999999":
            return self._create_response(
                status_code=200,
                json_data=Bundles.ALICE_JONES_9999999999,
            )

        return self._create_response(
            status_code=404,
            json_data={
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "not-found",
                        "diagnostics": "Patient not found",
                    }
                ],
            },
        )

    def post(
        self,
        url: str,
        data: str,
        **kwargs: Any,
    ) -> Response:
        """
        Handle HTTP POST requests for the stub.
        """
        headers = kwargs.get("headers", {})
        trace_id = headers.get("Ssp-TraceID", "no-trace-id")

        self._post_url = url
        self._post_headers = headers
        self._post_data = data
        self._post_timeout = kwargs.get("timeout")

        return self.access_record_structured(trace_id, data, headers)
