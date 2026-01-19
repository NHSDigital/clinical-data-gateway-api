"""FHIR Parameters resource."""

from typing import TypedDict

from fhir.identifier import Identifier


class Parameter(TypedDict):
    """FHIR Parameter type."""

    name: str
    valueIdentifier: Identifier


class Parameters(TypedDict):
    """FHIR Parameters resource."""

    resourceType: str
    parameter: list[Parameter]
