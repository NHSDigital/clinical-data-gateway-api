from typing import Annotated

from pydantic import Field

from fhir import Resource
from fhir.stu3.elements.issue import Issue


class OperationOutcome(Resource, resource_type="OperationOutcome"):
    """A FHIR STU3 OperationOutcome resource."""

    issue: Annotated[list[Issue], Field(frozen=True)]
