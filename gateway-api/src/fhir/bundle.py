"""FHIR Bundle resource."""

from typing import TypedDict

from fhir.patient import Patient


class BundleEntry(TypedDict):
    """FHIR Bundle entry."""

    fullUrl: str
    resource: Patient


class Bundle(TypedDict):
    """FHIR Bundle resource."""

    resourceType: str
    id: str
    type: str
    timestamp: str
    entry: list[BundleEntry]
