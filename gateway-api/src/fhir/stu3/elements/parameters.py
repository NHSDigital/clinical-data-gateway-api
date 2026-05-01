from abc import ABC
from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from fhir import Resource
from fhir.stu3 import PatientIdentifier


class Parameters(Resource, resource_type="Parameters"):
    """A FHIR STU3 Parameters resource."""

    @dataclass(frozen=True)
    class Parameter(ABC):
        """A FHIR STU3 Parameter resource."""

        valueIdentifier: Annotated[PatientIdentifier, Field(frozen=True)]

    class IdentityParameter(BaseModel):
        """
        A CDG-specific identity parameter carrying JWT claim fields in part elements.
        """

        model_config = ConfigDict(frozen=True)

        name: str
        part: list[dict[str, Any]]

    parameter: Annotated[
        list[Parameter | IdentityParameter], Field(frozen=True, min_length=1)
    ]
