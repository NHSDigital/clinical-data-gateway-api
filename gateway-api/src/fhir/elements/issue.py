from abc import ABC
from dataclasses import dataclass
from enum import StrEnum


class IssueSeverity(StrEnum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class IssueCode(StrEnum):
    INVALID = "invalid"
    EXCEPTION = "exception"


@dataclass(frozen=True)
class Issue(ABC):
    """
    A FHIR R4 OperationOutcome Issue element. See https://hl7.org/fhir/R4/datatypes.html#OperationOutcome.
    """

    severity: IssueSeverity
    code: IssueCode
    diagnostics: str | None = None
