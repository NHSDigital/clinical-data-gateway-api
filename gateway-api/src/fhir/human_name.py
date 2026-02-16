"""FHIR HumanName type."""

from typing import TypedDict

from fhir.period import Period


class HumanName(TypedDict):
    use: str
    family: str
    given: list[str]
    period: Period
