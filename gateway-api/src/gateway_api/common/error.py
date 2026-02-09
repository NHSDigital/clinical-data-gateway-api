import json
from dataclasses import dataclass
from http.client import BAD_REQUEST
from typing import TYPE_CHECKING

from flask import Response

if TYPE_CHECKING:
    from fhir.operation_outcome import OperationOutcome


@dataclass
class Error(Exception):
    message: str = "Internal Server Error"
    status_code: int = 500
    severity: str = "error"
    fhir_error_code: str = "exception"

    def build_response(self) -> Response:
        operation_outcome: OperationOutcome = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": self.severity,
                    "code": self.fhir_error_code,
                    "diagnostics": self.message,
                }
            ],
        }
        response = Response(
            response=json.dumps(operation_outcome),
            status=self.status_code,
            content_type="application/fhir+json",
        )
        return response


class CDGAPIErrors:
    INVALID_REQUEST_JSON = Error(
        "Invalid JSON body sent in request", status_code=BAD_REQUEST
    )

    MISSING_TRACE_ID = Error(
        'Missing or empty required header "Ssp-TraceID"', status_code=BAD_REQUEST
    )
    MISSING_ODS_CODE = Error(
        'Missing or empty required header "ODS-from"', status_code=BAD_REQUEST
    )
