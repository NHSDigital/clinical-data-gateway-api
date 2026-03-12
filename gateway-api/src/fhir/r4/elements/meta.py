import datetime
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field


@dataclass(frozen=True)
class Meta:
    """
    A FHIR R4 Meta element. See https://hl7.org/fhir/R4/datatypes.html#Meta.
    Attributes:
        version_id: The version id of the resource.
        last_updated: The last updated timestamp of the resource.
    """

    last_updated: Annotated[datetime.datetime | None, Field(alias="lastUpdated")] = None
    version_id: Annotated[str | None, Field(alias="versionId")] = None

    @classmethod
    def with_last_updated(cls, last_updated: datetime.datetime | None = None) -> "Meta":
        """
        Create a Meta instance with the provided last_updated timestamp.
        Args:
            last_updated: The last updated timestamp.
        Returns:
            A Meta instance with the specified last_updated.
        """
        return cls(
            last_updated=last_updated or datetime.datetime.now(tz=datetime.timezone.utc)
        )
