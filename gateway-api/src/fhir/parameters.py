"""FHIR Parameters resource."""

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from fhir.identifier import Identifier


class Parameter(TypedDict):
    name: str
    valueIdentifier: Identifier


class Parameters(TypedDict):
    resourceType: str
    parameter: list[Parameter]
