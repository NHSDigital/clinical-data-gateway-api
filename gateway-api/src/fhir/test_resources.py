import json
from typing import Any

import pytest
from pydantic import BaseModel

from .resources import Bundle, Patient, Resource


class TestResource:
    class _TestContainer(BaseModel):
        resource: Resource

    def test_resource_deserialisation(self) -> None:
        expected_system = "https://fhir.nhs.uk/Id/nhs-number"
        expected_nhs_number = "nhs_number"
        example_json = json.dumps(
            {
                "resource": {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": expected_system,
                            "value": expected_nhs_number,
                        }
                    ],
                }
            }
        )

        created_object = self._TestContainer.model_validate_json(example_json)
        assert isinstance(created_object.resource, Patient)

        created_patient = created_object.resource
        assert created_patient.identifier is not None
        assert created_patient.identifier[0].system == expected_system
        assert created_patient.identifier[0].value == expected_nhs_number

    def test_resource_deserialisation_unknown_resource(self) -> None:
        expected_resource_type = "UnknownResourceType"
        example_json = json.dumps(
            {
                "resource": {
                    "resourceType": expected_resource_type,
                }
            }
        )

        with pytest.raises(
            TypeError,
            match=f"Unknown resource type: {expected_resource_type}",
        ):
            self._TestContainer.model_validate_json(example_json)

    @pytest.mark.parametrize(
        "value",
        [
            pytest.param({"resource": {}}, id="No resourceType key"),
            pytest.param(
                {"resource": {"resourceType": None}},
                id="resourceType is defined as None",
            ),
        ],
    )
    def test_resource_deserialisation_without_resource_type(
        self, value: dict[str, Any]
    ) -> None:
        example_json = json.dumps(value)

        with pytest.raises(
            TypeError,
            match="resourceType is required for Resource validation.",
        ):
            self._TestContainer.model_validate_json(example_json)

    @pytest.mark.parametrize(
        ("json", "expected_error_message"),
        [
            pytest.param(
                json.dumps({"resourceType": "invalid", "type": "document"}),
                "Value error, Resource type 'invalid' does not match expected "
                "resource type 'Bundle'.",
                id="Invalid resource type",
            ),
            pytest.param(
                json.dumps({"resourceType": None, "type": "document"}),
                "1 validation error for Bundle\nresourceType\n  "
                "Input should be a valid string",
                id="Input should be a valid string",
            ),
            pytest.param(
                json.dumps({"type": "document"}),
                "1 validation error for Bundle\nresourceType\n  Field required",
                id="Missing resource type",
            ),
        ],
    )
    def test_deserialise_wrong_resource_type(
        self, json: str, expected_error_message: str
    ) -> None:
        with pytest.raises(
            ValueError,
            match=expected_error_message,
        ):
            Bundle.model_validate_json(json, strict=True)


class TestBundle:
    def test_create(self) -> None:
        """Test creating a Bundle resource."""
        expected_entry = Bundle.Entry(
            fullUrl="full",
            resource=Patient.create(
                identifier=[Patient.PatientIdentifier.from_nhs_number("nhs_number")]
            ),
        )

        bundle = Bundle.create(
            type="document",
            entry=[expected_entry],
        )

        assert bundle.bundle_type == "document"
        assert bundle.identifier is None
        assert bundle.entries == [expected_entry]

    def test_create_without_entries(self) -> None:
        """Test creating a Bundle resource without entries."""
        bundle = Bundle.empty("document")

        assert bundle.bundle_type == "document"
        assert bundle.identifier is None
        assert bundle.entries is None

    expected_resource = Patient.create(
        identifier=[Patient.PatientIdentifier.from_nhs_number("nhs_number")]
    )

    @pytest.mark.parametrize(
        ("entries", "expected_results"),
        [
            pytest.param(
                [
                    Bundle.Entry(
                        fullUrl="fullUrl",
                        resource=expected_resource,
                    ),
                    Bundle.Entry(
                        fullUrl="fullUrl",
                        resource=expected_resource,
                    ),
                ],
                [expected_resource, expected_resource],
                id="Duplicate resources",
            ),
            pytest.param(
                [
                    Bundle.Entry(
                        fullUrl="fullUrl",
                        resource=expected_resource,
                    ),
                ],
                [expected_resource],
                id="Single resource",
            ),
        ],
    )
    def test_find_resources(
        self, entries: list[Bundle.Entry], expected_results: list[Resource]
    ) -> None:
        bundle = Bundle.create(type="document", entry=entries)

        result = bundle.find_resources(Patient)
        assert result == expected_results

    @pytest.mark.parametrize(
        "bundle",
        [
            pytest.param(Bundle.empty("document"), id="Bundle has no entries at all"),
            pytest.param(
                Bundle.create(type="document", entry=[]),
                id="Bundle has an empty entries list",
            ),
            pytest.param(
                Bundle.create(
                    type="document",
                    entry=[
                        Bundle.Entry(
                            fullUrl="fullUrl",
                            resource=Bundle.empty("document"),
                        ),
                    ],
                ),
                id="different_resource_type",
            ),
        ],
    )
    def test_find_resources_returns_empty_list(self, bundle: Bundle) -> None:
        """
        Test that find_resources returns an empty list when no matching resources exist.
        """
        result = bundle.find_resources(Patient)
        assert result == []


class TestPatient:
    def test_create(self) -> None:
        """Test creating a Patient resource."""
        nhs_number = "1234567890"

        expected_identifier = Patient.PatientIdentifier.from_nhs_number(nhs_number)
        patient = Patient.create(identifier=[expected_identifier])

        assert patient.identifier[0] == expected_identifier

    def test_create_with_general_practitioner_identifier(self) -> None:
        """Test creating a Patient resource with an ODS-coded practitioner org."""
        nhs_number = "1234567890"
        ods_code = "A12345"

        patient = Patient.create(
            identifier=[Patient.PatientIdentifier.from_nhs_number(nhs_number)],
            generalPractitioner=[
                Patient.GeneralPractitioner(
                    type="Organization",
                    identifier=Patient.GeneralPractitioner.OrganizationIdentifier(
                        system="https://fhir.nhs.uk/Id/ods-organization-code",
                        value=ods_code,
                    ),
                )
            ],
        )

        assert patient.generalPractitioner is not None
        assert patient.generalPractitioner[0].reference_type == "Organization"
        assert patient.generalPractitioner[0].identifier is not None
        assert (
            patient.generalPractitioner[0].identifier.system
            == "https://fhir.nhs.uk/Id/ods-organization-code"
        )
        assert patient.generalPractitioner[0].identifier.value == ods_code

    def test_create_with_invalid_patient_identifier_system_raises_error(self) -> None:
        """Test invalid patient identifier systems are rejected."""
        with pytest.raises(
            ValueError,
            match=(
                "Identifier system 'https://example.org/invalid' does not match "
                "expected system 'https://fhir.nhs.uk/Id/nhs-number'."
            ),
        ):
            Patient.model_validate(
                {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": "https://example.org/invalid",
                            "value": "1234567890",
                        }
                    ],
                }
            )

    def test_create_with_invalid_general_practitioner_identifier_system_raises_error(
        self,
    ) -> None:
        """Test invalid practitioner organization identifier systems are rejected."""
        with pytest.raises(
            ValueError,
            match=(
                "Identifier system 'https://example.org/invalid' does not match "
                "expected system 'https://fhir.nhs.uk/Id/ods-organization-code'."
            ),
        ):
            Patient.create(
                identifier=[Patient.PatientIdentifier.from_nhs_number("1234567890")],
                generalPractitioner=[
                    Patient.GeneralPractitioner(
                        type="Organization",
                        identifier=(
                            Patient.GeneralPractitioner.OrganizationIdentifier(
                                system="https://example.org/invalid",
                                value="A12345",
                            )
                        ),
                    )
                ],
            )

    def test_model_dump_json_excludes_none_general_practitioner(self) -> None:
        """Test JSON output omits optional fields when they are None."""
        patient = Patient.create(
            identifier=[Patient.PatientIdentifier.from_nhs_number("1234567890")]
        )

        payload = json.loads(patient.model_dump_json())

        assert payload["resourceType"] == "Patient"
        assert "generalPractitioner" not in payload


class TestPatientIdentifier:
    def test_create_from_nhs_number(self) -> None:
        """Test creating a PatientIdentifier from an NHS number."""
        nhs_number = "1234567890"
        identifier = Patient.PatientIdentifier.from_nhs_number(nhs_number)

        assert identifier.system == "https://fhir.nhs.uk/Id/nhs-number"
        assert identifier.value == nhs_number
