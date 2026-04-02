from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from fhir import Resource
from fhir.r4.elements.identifier import (
    AgnosticUserRoleIdentifier,
    SDSRoleProfileIDIdentifier,
    SDSUserIDIdentifier,
)


@dataclass(frozen=True)
class HumanName:
    family: str
    given: list[str] | None = None
    prefix: list[str] | None = None


class Practitioner(Resource, resource_type="Practitioner"):
    """A FHIR R4 Practitioner resource."""

    name: Annotated[list[HumanName], Field(frozen=True, min_length=1)]
    identifier: Annotated[
        list[
            SDSUserIDIdentifier
            | SDSRoleProfileIDIdentifier
            | AgnosticUserRoleIdentifier
        ],
        Field(frozen=True, min_length=1),
    ]

    id: str
