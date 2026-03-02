"""FHIR GeneralPractitioner type."""

from typing import TypedDict

from fhir.period import Period


class GeneralPractitionerIdentifier(TypedDict):
    """Identifier for GeneralPractitioner"""

    system: str
    value: str
    period: Period


class GeneralPractitioner(TypedDict):
    """FHIR GeneralPractitioner reference."""

    id: str
    type: str
    identifier: GeneralPractitionerIdentifier
