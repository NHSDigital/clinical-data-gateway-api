from typing import Annotated

from pydantic import ConfigDict, Field

from fhir import Resource

from ..elements.identifier import (
    AgnosticDeviceIdentifier,
    ASIDIdentifier,
)


class Device(Resource, resource_type="Device"):
    """A FHIR R4 Device resource."""

    model_config = ConfigDict(extra="allow")

    identifier: Annotated[
        list[ASIDIdentifier | AgnosticDeviceIdentifier],
        Field(frozen=True, min_length=1),
    ]
