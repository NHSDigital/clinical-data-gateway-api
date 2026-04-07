import traceback
from dataclasses import dataclass
from http.client import BAD_GATEWAY, BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND

from fhir.stu3 import Issue, IssueCode, IssueSeverity, OperationOutcome


@dataclass
class AbstractCDGError(Exception):
    """
    Abstract class for all errors.
    """

    _message: str
    status_code: int
    error_code: IssueCode
    severity: IssueSeverity = IssueSeverity.ERROR

    def __init__(self, **additional_details: str):
        """
        Pass additional details while instantiating the object. These will be used to
        complete the error message with relevant information, such as NHS number.
        """
        self.additional_details = additional_details
        super().__init__(self)

    @property
    def operation_outcome(self) -> OperationOutcome:
        operation_outcome = OperationOutcome.create(
            issue=[
                Issue(
                    severity=self.severity,
                    code=self.error_code,
                    diagnostics=self.message,
                )
            ]
        )
        return operation_outcome

    def log(self) -> None:
        print(traceback.format_exc(), flush=True)

    @property
    def message(self) -> str:
        return self._message.format(**self.additional_details)

    def __str__(self) -> str:
        return self.message


class InvalidRequestJSONError(AbstractCDGError):
    _message = "Invalid JSON body sent in request"
    error_code = IssueCode.INVALID
    status_code = BAD_REQUEST


class MissingOrEmptyHeaderError(AbstractCDGError):
    _message = 'Missing or empty required header "{header}"'
    status_code = BAD_REQUEST
    error_code = IssueCode.EXCEPTION


class NoCurrentProviderError(AbstractCDGError):
    _message = "PDS patient {nhs_number} did not contain a current provider ODS code"
    status_code = NOT_FOUND
    error_code = IssueCode.EXCEPTION


class NoOrganisationFoundError(AbstractCDGError):
    _message = "No SDS org found for {org_type} ODS code {ods_code}"
    status_code = NOT_FOUND
    error_code = IssueCode.EXCEPTION


class NoAsidFoundError(AbstractCDGError):
    _message = (
        "SDS result for {org_type} ODS code {ods_code} did not contain a current ASID"
    )
    status_code = NOT_FOUND
    error_code = IssueCode.EXCEPTION


class NoCurrentEndpointError(AbstractCDGError):
    _message = (
        "SDS result for provider ODS code {provider_ods} did not contain "
        "a current endpoint"
    )
    status_code = NOT_FOUND
    error_code = IssueCode.EXCEPTION


class PdsRequestFailedError(AbstractCDGError):
    _message = "PDS FHIR API request failed: {error_reason}"
    status_code = BAD_GATEWAY
    error_code = IssueCode.EXCEPTION


class SdsRequestFailedError(AbstractCDGError):
    _message = "SDS FHIR API request failed: {error_reason}"
    status_code = BAD_GATEWAY
    error_code = IssueCode.EXCEPTION


class ProviderRequestFailedError(AbstractCDGError):
    _message = "Provider request failed: {error_reason}"
    status_code = BAD_GATEWAY
    error_code = IssueCode.EXCEPTION


class JWTValidationError(AbstractCDGError):
    _message = "{error_details}"
    status_code = BAD_REQUEST
    error_code = IssueCode.INVALID


class UnexpectedError(AbstractCDGError):
    _message = "Internal Server Error: {traceback}"
    status_code = INTERNAL_SERVER_ERROR
    severity = IssueSeverity.ERROR
    error_code = IssueCode.EXCEPTION
