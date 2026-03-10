"""FHIR Bundle resource."""

from typing import TypedDict

from fhir.patient import PatientTypedDict


class BundleEntry(TypedDict):
    fullUrl: str
    resource: PatientTypedDict


class Bundle(TypedDict):
    resourceType: str
    id: str
    type: str
    timestamp: str
    entry: list[BundleEntry]
