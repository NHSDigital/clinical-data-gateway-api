"""FHIR Patient resource."""

from typing import NotRequired, TypedDict

from fhir.general_practitioner import GeneralPractitioner
from fhir.human_name import HumanName
from fhir.identifier import Identifier


class Patient(TypedDict):
    resourceType: str
    id: str
    identifier: list[Identifier]
    name: list[HumanName]
    gender: str
    birthDate: str
    generalPractitioner: NotRequired[list[GeneralPractitioner]]
