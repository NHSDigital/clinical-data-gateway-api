from typing import Annotated

from pydantic import Field

from fhir import Resource

from ..elements.identifier import ASIDIdentifier, PartyKeyIdentifier


class Device(Resource, resource_type="Device"):
    """A FHIR R4 Device resource."""

    identifier: Annotated[
        list[ASIDIdentifier | PartyKeyIdentifier], Field(frozen=True, min_length=1)
    ]
