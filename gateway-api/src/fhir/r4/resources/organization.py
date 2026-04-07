from typing import Annotated

from pydantic import Field

from fhir import Resource

from ..elements.identifier import OrganizationIdentifier


class Organization(Resource, resource_type="Organization"):
    """A FHIR R4 Organization resource."""

    name: str
    identifier: Annotated[
        list[OrganizationIdentifier], Field(frozen=True, min_length=1)
    ]

    @classmethod
    def from_ods_code(cls, ods_code: str, name: str) -> "Organization":
        return cls.create(
            name=name,
            identifier=[
                OrganizationIdentifier(
                    value=ods_code,
                )
            ],
        )
