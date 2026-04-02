import uuid

from fhir.elements.identifier import Identifier


class UUIDIdentifier(Identifier, expected_system="https://tools.ietf.org/html/rfc4122"):
    """A UUID identifier utilising the standard RFC 4122 system."""

    def __init__(self, value: uuid.UUID | None = None):
        super().__init__(
            value=str(value or uuid.uuid4()),
            system=self._expected_system,
        )


class PatientIdentifier(
    Identifier, expected_system="https://fhir.nhs.uk/Id/nhs-number"
):
    """A FHIR R4 Patient Identifier utilising the NHS Number system."""

    def __init__(self, value: str):
        super().__init__(value=value, system=self._expected_system)

    @classmethod
    def from_nhs_number(cls, nhs_number: str) -> "PatientIdentifier":
        """Create a PatientIdentifier from an NHS number."""
        return cls(value=nhs_number)


class ASIDIdentifier(Identifier, expected_system="https://fhir.nhs.uk/Id/nhsSpineASID"):
    """A FHIR R4 ASID Identifier."""


class PartyKeyIdentifier(
    Identifier, expected_system="https://fhir.nhs.uk/Id/nhsMhsPartyKey"
):
    """A FHIR R4 Party Key Identifier."""


class OrganizationIdentifier(
    Identifier, expected_system="https://fhir.nhs.uk/Id/ods-organization-code"
):
    """
    A FHIR R4 Organization Identifier utilising the ODS Organization Code
    system.
    """
