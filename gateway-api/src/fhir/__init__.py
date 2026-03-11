"""FHIR data types and resources."""

from fhir.bundle import BundleEntry, BundleTypedDict
from fhir.general_practitioner import GeneralPractitioner
from fhir.human_name import HumanName
from fhir.identifier import Identifier
from fhir.operation_outcome import OperationOutcome, OperationOutcomeIssue
from fhir.parameters import Parameter, ParametersTypedDict
from fhir.patient import PatientTypedDict

__all__ = [
    "BundleTypedDict",
    "BundleEntry",
    "HumanName",
    "Identifier",
    "OperationOutcome",
    "OperationOutcomeIssue",
    "Parameter",
    "ParametersTypedDict",
    "PatientTypedDict",
    "GeneralPractitioner",
]
