from typing import Annotated

from pydantic import Field

from fhir import Resource

from ..elements.identifier import PatientIdentifier
from ..elements.reference import GeneralPractitioner


class Patient(Resource, resource_type="Patient"):
    """A FHIR R4 Patient resource."""

    identifier: Annotated[list[PatientIdentifier], Field(frozen=True, min_length=1)]

    @property
    def nhs_number(self) -> str:
        return self.identifier[0].value

    generalPractitioner: Annotated[
        list[GeneralPractitioner] | None, Field(frozen=True)
    ] = None

    @property
    def gp_ods_code(self) -> str | None:
        if not self.generalPractitioner:
            return None

        return self.generalPractitioner[0].identifier.value
