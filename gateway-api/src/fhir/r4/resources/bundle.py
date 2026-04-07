from typing import Annotated, Literal

from pydantic import Field

from fhir import Resource

from ..elements.entry import Entry
from ..elements.identifier import UUIDIdentifier

type BundleType = Literal["document", "transaction", "searchset", "collection"]


class Bundle(Resource, resource_type="Bundle"):
    """A FHIR R4 Bundle resource."""

    bundle_type: BundleType = Field(alias="type", frozen=True)
    identifier: Annotated[UUIDIdentifier | None, Field(frozen=True)] = None
    entries: list[Entry] | None = Field(None, frozen=True, alias="entry")

    def find_resources[T: Resource](self, t: type[T]) -> list[T]:
        """
        Find all resources of a given type in the bundle entries. If the bundle has no
        entries, an empty list is returned.
        Args:
            t: The resource type to search for.
        Returns:
            A list of resources of the specified type.
        """
        return [
            entry.resource
            for entry in self.entries or []
            if isinstance(entry.resource, t)
        ]

    @classmethod
    def empty(cls, bundle_type: BundleType) -> "Bundle":
        """Create an empty Bundle of the specified type."""
        return cls.create(type=bundle_type, entry=None)
