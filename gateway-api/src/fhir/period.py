"""FHIR Period type."""

from typing import NotRequired, TypedDict


class Period(TypedDict, total=False):
    """FHIR Period type."""

    start: str
    end: NotRequired[str]
