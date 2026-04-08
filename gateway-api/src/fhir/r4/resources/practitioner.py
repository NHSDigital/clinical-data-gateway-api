from typing import Annotated

from pydantic import Field

from fhir import Resource
from fhir.r4.elements.human_name import HumanName
from fhir.r4.elements.identifier import (
    AgnosticUserRoleIdentifier,
    SDSRoleProfileIDIdentifier,
    SDSUserIDIdentifier,
)


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
