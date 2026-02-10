import json
from dataclasses import dataclass
from http.client import INTERNAL_SERVER_ERROR
from typing import TYPE_CHECKING

from flask import Response

if TYPE_CHECKING:
    from fhir.operation_outcome import OperationOutcome


@dataclass
class BaseError(Exception):
    _message = "Internal Server Error"
    status_code: int = INTERNAL_SERVER_ERROR
    severity: str = "error"
    error_code: str = "exception"

    def __init__(self, **additional_details: str):
        self.additional_details = additional_details
        super().__init__(self)

    def build_response(self) -> Response:
        operation_outcome: OperationOutcome = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": self.severity,
                    "code": self.error_code,
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

    def log(self) -> None:
        print(self)

    @property
    def message(self) -> str:
        return self._message.format(**self.additional_details)

    def __str__(self) -> str:
        return self.message


class NoPatientFound(BaseError):
    _message = "No PDS patient found for NHS number {nhs_number}"
    status_code = 400


class InvalidRequestJSON(BaseError):
    _message = "Invalid JSON body sent in request"
    status_code = 400


class MissingOrEmptyHeader(BaseError):
    _message = 'Missing or empty required header "{header}"'
    status_code = 400


class NoCurrentProvider(BaseError):
    _message = "PDS patient {nhs_number} did not contain a current provider ODS code"
    status_code = 404


class NoOrganisationFound(BaseError):
    _message = "No SDS org found for {org_type} ODS code {ods_code}"
    status_code = 404


class NoAsidFound(BaseError):
    _message = (
        "SDS result for {org_type} ODS code {ods_code} did not contain a current ASID"
    )
    status_code = 404


class NoCurrentEndpoint(BaseError):
    _message = (
        "SDS result for provider ODS code {provider_ods} did not contain "
        "a current endpoint"
    )
    status_code = 404
