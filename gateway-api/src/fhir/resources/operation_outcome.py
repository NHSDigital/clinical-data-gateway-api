from typing import Annotated

from pydantic import Field

from ..elements.issue import Issue
from .resource import Resource


class OperationOutcome(Resource, resource_type="OperationOutcome"):
    """A FHIR R4 OperationOutcome resource."""

    issue: Annotated[list[Issue], Field(frozen=True)]
