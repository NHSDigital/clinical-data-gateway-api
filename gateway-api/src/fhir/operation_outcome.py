"""FHIR OperationOutcome resource."""

from typing import TypedDict


class OperationOutcomeIssue(TypedDict):
    severity: str
    code: str
    diagnostics: str


class OperationOutcome(TypedDict):
    resourceType: str
    issue: list[OperationOutcomeIssue]
