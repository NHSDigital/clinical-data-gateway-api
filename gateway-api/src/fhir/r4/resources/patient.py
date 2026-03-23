from typing import Annotated

from pydantic import Field

from fhir import Resource

from ..elements.identifier import Identifier
from ..elements.reference import Reference


class Patient(Resource, resource_type="Patient"):
    """A FHIR R4 Patient resource."""

    class PatientIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhs-number"
    ):
        """A FHIR R4 Patient Identifier utilising the NHS Number system."""

        def __init__(self, value: str):
            super().__init__(value=value, system=self._expected_system)

        @classmethod
        def from_nhs_number(cls, nhs_number: str) -> "Patient.PatientIdentifier":
            """Create a PatientIdentifier from an NHS number."""
            return cls(value=nhs_number)

    identifier: Annotated[list[PatientIdentifier], Field(frozen=True, min_length=1)]

    @property
    def nhs_number(self) -> str:
        return self.identifier[0].value

    class GeneralPractitioner(Reference, reference_type="Organization"):
        class OrganizationIdentifier(
            Identifier, expected_system="https://fhir.nhs.uk/Id/ods-organization-code"
        ):
            """
            A FHIR R4 Organization Identifier utilising the ODS Organization Code
            system.
            """

        identifier: Annotated[OrganizationIdentifier, Field(frozen=True)]

    generalPractitioner: Annotated[
        list[GeneralPractitioner] | None, Field(frozen=True)
    ] = None

    @property
    def gp_ods_code(self) -> str | None:
        if not self.generalPractitioner:
            return None

        return self.generalPractitioner[0].identifier.value
