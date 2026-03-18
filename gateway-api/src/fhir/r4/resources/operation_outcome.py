from typing import Annotated

from pydantic import Field

from fhir import Resource

from ..elements.issue import Issue


class OperationOutcome(Resource, resource_type="OperationOutcome"):
    """A FHIR R4 OperationOutcome resource."""

    issue: Annotated[list[Issue], Field(frozen=True)]
