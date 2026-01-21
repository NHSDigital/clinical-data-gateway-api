"""FHIR Identifier type."""

from typing import TypedDict


class Identifier(TypedDict):
    system: str
    value: str
