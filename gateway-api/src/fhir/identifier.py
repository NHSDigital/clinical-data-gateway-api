"""FHIR Identifier type."""

from typing import TypedDict


class Identifier(TypedDict):
    """FHIR Identifier type."""

    system: str
    value: str
