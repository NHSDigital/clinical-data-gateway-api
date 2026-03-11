"""FHIR Parameters resource."""

from typing import TypedDict

from fhir.identifier import Identifier


class Parameter(TypedDict):
    name: str
    valueIdentifier: Identifier


class ParametersTypedDict(TypedDict):
    resourceType: str
    parameter: list[Parameter]
