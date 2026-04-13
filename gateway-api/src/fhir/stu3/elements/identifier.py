from fhir.elements.identifier import Identifier


class PatientIdentifier(
    Identifier, expected_system="https://fhir.nhs.uk/Id/nhs-number"
):
    """A FHIR STU3 Patient Identifier utilising the NHS Number system."""

    def __init__(self, value: str):
        super().__init__(value=value, system=self._expected_system)

    @classmethod
    def from_nhs_number(cls, nhs_number: str) -> "PatientIdentifier":
        """Create a PatientIdentifier from an NHS number."""
        return cls(value=nhs_number)
