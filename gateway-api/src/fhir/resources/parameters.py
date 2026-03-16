from abc import ABC
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from ..elements.identifier import NHSNumberValueIdentifier
from .resource import Resource


class Parameters(Resource, resource_type="Parameters"):
    """A FHIR R4 Parameters resource."""

    @dataclass(frozen=True)
    class Parameter(ABC):
        """A FHIR R4 Parameter resource."""

        valueIdentifier: Annotated[NHSNumberValueIdentifier, Field(frozen=True)]

    parameter: Annotated[list[Parameter], Field(frozen=True, min_length=1)]
