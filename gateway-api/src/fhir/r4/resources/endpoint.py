from pydantic import Field

from ...resources.resource import Resource


class Endpoint(Resource, resource_type="Endpoint"):
    """A FHIR R4 Endpoint resource."""

    address: str | None = Field(None, frozen=True)
