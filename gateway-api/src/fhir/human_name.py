"""FHIR HumanName type."""

from typing import TypedDict


class HumanName(TypedDict):
    use: str
    family: str
    given: list[str]
