from typing import Annotated

from pydantic import Field

from ..elements.identifier import Identifier
from .resource import Resource


class Device(Resource, resource_type="Device"):
    """A FHIR R4 Device resource."""

    class ASIDIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhsSpineASID"
    ):
        """A FHIR R4 ASID Identifier."""

    class PartyKeyIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhsMhsPartyKey"
    ):
        """A FHIR R4 Party Key Identifier."""

    identifier: Annotated[
        list[ASIDIdentifier | PartyKeyIdentifier], Field(frozen=True, min_length=1)
    ]
