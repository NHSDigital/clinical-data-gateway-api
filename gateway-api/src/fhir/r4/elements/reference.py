from typing import Annotated, ClassVar

from pydantic import BaseModel, Field, model_validator

from .identifier import Identifier, OrganizationIdentifier


class Reference(BaseModel):
    """A FHIR R4 Reference base class."""

    _expected_reference_type: ClassVar[str] = "__unknown__"

    identifier: Identifier
    reference_type: str = Field(alias="type")

    reference: str | None = None
    display: str | None = None

    def __init_subclass__(cls, reference_type: str) -> None:
        cls._expected_reference_type = reference_type
        super().__init_subclass__()

    @model_validator(mode="after")
    def validate_reference_type(self) -> "Reference":
        if self.reference_type != self._expected_reference_type:
            raise ValueError(
                f"Reference type '{self.reference_type}' does not match expected "
                f"type '{self._expected_reference_type}'."
            )
        return self


class GeneralPractitioner(Reference, reference_type="Organization"):
    identifier: Annotated[OrganizationIdentifier, Field(frozen=True)]
