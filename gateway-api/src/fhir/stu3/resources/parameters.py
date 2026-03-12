from abc import ABC
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from ...r4.elements.identifier import NHSNumberValueIdentifier
from ...resources.resource import Resource


class Parameters(Resource, resource_type="Parameters"):
    """A FHIR STU3 Parameters resource."""

    @dataclass(frozen=True)
    class Parameter(ABC):
        """A FHIR STU3 Parameter resource."""

        valueIdentifier: Annotated[NHSNumberValueIdentifier, Field(frozen=True)]

    parameter: Annotated[list[Parameter], Field(frozen=True)]
