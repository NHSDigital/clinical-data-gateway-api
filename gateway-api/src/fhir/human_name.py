"""FHIR HumanName type."""

from typing import TypedDict


class HumanName(TypedDict):
    """FHIR HumanName type."""

    use: str
    family: str
    given: list[str]
