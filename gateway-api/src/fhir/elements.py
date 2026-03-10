import datetime
import uuid
from abc import ABC
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, ClassVar

from pydantic import Field, model_validator


@dataclass(frozen=True)
class Meta:
    """
    A FHIR R4 Meta element. See https://hl7.org/fhir/R4/datatypes.html#Meta.
    Attributes:
        version_id: The version id of the resource.
        last_updated: The last updated timestamp of the resource.
    """

    last_updated: Annotated[datetime.datetime | None, Field(alias="lastUpdated")] = None
    version_id: Annotated[str | None, Field(alias="versionId")] = None

    @classmethod
    def with_last_updated(cls, last_updated: datetime.datetime | None = None) -> "Meta":
        """
        Create a Meta instance with the provided last_updated timestamp.
        Args:
            last_updated: The last updated timestamp.
        Returns:
            A Meta instance with the specified last_updated.
        """
        return cls(
            last_updated=last_updated or datetime.datetime.now(tz=datetime.timezone.utc)
        )


@dataclass(frozen=True)
class Identifier(ABC):
    """
    A FHIR R4 Identifier element. See https://hl7.org/fhir/R4/datatypes.html#Identifier.
    Attributes:
        system: The namespace for the identifier value.
        value: The value that is unique within the system.
    """

    _expected_system: ClassVar[str] = "__unknown__"

    value: str
    system: str

    @model_validator(mode="after")
    def validate_system(self) -> "Identifier":
        if self.system != self._expected_system:
            raise ValueError(
                f"Identifier system '{self.system}' does not match expected "
                f"system '{self._expected_system}'."
            )
        return self

    @classmethod
    def __init_subclass__(cls, expected_system: str) -> None:
        cls._expected_system = expected_system


class UUIDIdentifier(Identifier, expected_system="https://tools.ietf.org/html/rfc4122"):
    """A UUID identifier utilising the standard RFC 4122 system."""

    def __init__(self, value: uuid.UUID | None = None):
        super().__init__(
            value=str(value or uuid.uuid4()),
            system=self._expected_system,
        )


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
