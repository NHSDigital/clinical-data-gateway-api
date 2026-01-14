"""FHIR Bundle resource."""

from typing import TypedDict

from fhir.patient import Patient


class BundleEntry(TypedDict):
    fullUrl: str
    resource: Patient


class Bundle(TypedDict):
    resourceType: str
    id: str
    type: str
    timestamp: str
    entry: list[BundleEntry]
