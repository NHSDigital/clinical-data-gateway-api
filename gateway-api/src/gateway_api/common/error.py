import json
import traceback
from dataclasses import dataclass
from enum import StrEnum
from http.client import BAD_GATEWAY, BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND
from typing import TYPE_CHECKING

from flask import Response

if TYPE_CHECKING:
    from fhir.operation_outcome import OperationOutcome


class ErrorCode(StrEnum):
    INVALID = "invalid"
    EXCEPTION = "exception"


@dataclass
class AbstractCDGError(Exception):
    """
    Abstract class for all errors.
    """

    _message: str
    status_code: int
    error_code: ErrorCode
    severity: str = "error"

    def __init__(self, **additional_details: str):
        """
        Pass additional details while instantiating the object. These will be used to
        complete the error message with relevant information, such as NHS number.
        """
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
        print(traceback.format_exc(), flush=True)

    @property
    def message(self) -> str:
        return self._message.format(**self.additional_details)

    def __str__(self) -> str:
        return self.message


class InvalidRequestJSONError(AbstractCDGError):
    _message = "Invalid JSON body sent in request"
    error_code = ErrorCode.INVALID
    status_code = BAD_REQUEST


class MissingOrEmptyHeaderError(AbstractCDGError):
    _message = 'Missing or empty required header "{header}"'
    status_code = BAD_REQUEST
    error_code = ErrorCode.EXCEPTION


class NoCurrentProviderError(AbstractCDGError):
    _message = "PDS patient {nhs_number} did not contain a current provider ODS code"
    status_code = NOT_FOUND
    error_code = ErrorCode.EXCEPTION


class NoOrganisationFoundError(AbstractCDGError):
    _message = "No SDS org found for {org_type} ODS code {ods_code}"
    status_code = NOT_FOUND
    error_code = ErrorCode.EXCEPTION


class NoAsidFoundError(AbstractCDGError):
    _message = (
        "SDS result for {org_type} ODS code {ods_code} did not contain a current ASID"
    )
    status_code = NOT_FOUND
    error_code = ErrorCode.EXCEPTION


class NoCurrentEndpointError(AbstractCDGError):
    _message = (
        "SDS result for provider ODS code {provider_ods} did not contain "
        "a current endpoint"
    )
    status_code = NOT_FOUND
    error_code = ErrorCode.EXCEPTION


class PdsRequestFailedError(AbstractCDGError):
    _message = "PDS FHIR API request failed: {error_reason}"
    status_code = BAD_GATEWAY
    error_code = ErrorCode.EXCEPTION


class ProviderRequestFailedError(AbstractCDGError):
    _message = "Provider request failed: {error_reason}"
    status_code = BAD_GATEWAY
    error_code = ErrorCode.EXCEPTION


class JWTValidationError(AbstractCDGError):
    _message = "{error_details}"
    status_code = BAD_REQUEST
    error_code = ErrorCode.INVALID


class UnexpectedError(AbstractCDGError):
    _message = "Internal Server Error: {traceback}"
    status_code = INTERNAL_SERVER_ERROR
    severity = "error"
    error_code = ErrorCode.EXCEPTION
