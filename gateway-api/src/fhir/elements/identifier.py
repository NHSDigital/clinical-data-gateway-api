from abc import ABC
from dataclasses import dataclass
from typing import ClassVar

from pydantic import model_validator


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
