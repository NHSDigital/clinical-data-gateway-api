import json

import pytest
from pydantic import ValidationError

from fhir import Resource
from fhir.r4 import (
    ASIDIdentifier,
    Bundle,
    Device,
    Endpoint,
    Entry,
    GeneralPractitioner,
    OrganizationIdentifier,
    Patient,
    PatientIdentifier,
    Practitioner,
)
from fhir.r4.elements.human_name import HumanName
from fhir.r4.elements.identifier import (
    AgnosticUserRoleIdentifier,
    SDSRoleProfileIDIdentifier,
    SDSUserIDIdentifier,
)
from fhir.r4.resources.organization import Organization


class TestBundle:
    def test_create(self) -> None:
        """Test creating a Bundle resource."""
        expected_entry = Entry(
            fullUrl="full",
            resource=Patient.create(
                identifier=[PatientIdentifier.from_nhs_number("nhs_number")]
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
        identifier=[PatientIdentifier.from_nhs_number("nhs_number")]
    )

    @pytest.mark.parametrize(
        ("entries", "expected_results"),
        [
            pytest.param(
                [
                    Entry(
                        fullUrl="fullUrl",
                        resource=expected_resource,
                    ),
                    Entry(
                        fullUrl="fullUrl",
                        resource=expected_resource,
                    ),
                ],
                [expected_resource, expected_resource],
                id="Duplicate resources",
            ),
            pytest.param(
                [
                    Entry(
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
        self, entries: list[Entry], expected_results: list[Resource]
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
                        Entry(
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

        expected_identifier = PatientIdentifier.from_nhs_number(nhs_number)
        patient = Patient.create(identifier=[expected_identifier])

        assert patient.identifier[0] == expected_identifier

    def test_create_with_general_practitioner_identifier(self) -> None:
        """Test creating a Patient resource with an ODS-coded practitioner org."""
        nhs_number = "1234567890"
        ods_code = "A12345"

        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number(nhs_number)],
            generalPractitioner=[
                GeneralPractitioner(
                    type="Organization",
                    identifier=OrganizationIdentifier(
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

    def test_model_dump_json_excludes_none_general_practitioner(self) -> None:
        """Test JSON output omits optional fields when they are None."""
        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number("1234567890")]
        )

        payload = json.loads(patient.model_dump_json())

        assert payload["resourceType"] == "Patient"
        assert "generalPractitioner" not in payload


class TestPatientIdentifier:
    def test_create_from_nhs_number(self) -> None:
        """Test creating a PatientIdentifier from an NHS number."""
        nhs_number = "1234567890"
        identifier = PatientIdentifier.from_nhs_number(nhs_number)

        assert identifier.system == "https://fhir.nhs.uk/Id/nhs-number", (
            "system should be the NHS number URI"
        )
        assert identifier.value == nhs_number, "value should match the NHS number"

    def test_create_with_constructor(self) -> None:
        identifier = PatientIdentifier(value="0000000000")

        assert identifier.system == "https://fhir.nhs.uk/Id/nhs-number", (
            "system should be populated from _expected_system"
        )
        assert identifier.value == "0000000000", "value should be '0000000000'"

    def test_expected_system_class_var(self) -> None:
        assert PatientIdentifier._expected_system == (
            "https://fhir.nhs.uk/Id/nhs-number"
        ), "_expected_system should be the NHS number URI"


class TestPatientNhsNumber:
    def test_nhs_number_property(self) -> None:
        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number("9876543210")]
        )

        assert patient.nhs_number == "9876543210", (
            "nhs_number property should return the first identifier value"
        )


class TestPatientGpOdsCode:
    def test_gp_ods_code_with_practitioner(self) -> None:
        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number("1234567890")],
            generalPractitioner=[
                GeneralPractitioner(
                    type="Organization",
                    identifier=OrganizationIdentifier(
                        value="B81001",
                    ),
                )
            ],
        )

        assert patient.gp_ods_code == "B81001", (
            "gp_ods_code should return the ODS code from the first generalPractitioner"
        )

    def test_gp_ods_code_without_practitioner(self) -> None:
        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number("1234567890")]
        )

        assert patient.gp_ods_code is None, (
            "gp_ods_code should be None when generalPractitioner is absent"
        )

    def test_gp_ods_code_with_empty_practitioner_list(self) -> None:
        patient = Patient.create(
            identifier=[PatientIdentifier.from_nhs_number("1234567890")],
            generalPractitioner=[],
        )

        assert patient.gp_ods_code is None, (
            "gp_ods_code should be None when generalPractitioner list is empty"
        )


class TestPatientModelValidate:
    def test_valid_patient(self) -> None:
        patient = Patient.model_validate(
            {
                "resourceType": "Patient",
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "1234567890",
                    }
                ],
            }
        )

        assert patient.nhs_number == "1234567890", (
            "nhs_number should be parsed from JSON"
        )

    def test_valid_patient_with_general_practitioner(self) -> None:
        patient = Patient.model_validate(
            {
                "resourceType": "Patient",
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "1234567890",
                    }
                ],
                "generalPractitioner": [
                    {
                        "type": "Organization",
                        "identifier": {
                            "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                            "value": "A12345",
                        },
                    }
                ],
            }
        )

        assert patient.gp_ods_code == "A12345", "gp_ods_code should be parsed from JSON"

    def test_missing_identifier_fails(self) -> None:
        with pytest.raises(ValidationError, match="identifier"):
            Patient.model_validate({"resourceType": "Patient"})

    def test_empty_identifier_list_fails(self) -> None:
        with pytest.raises(ValidationError, match="too_short"):
            Patient.model_validate({"resourceType": "Patient", "identifier": []})

    def test_invalid_gp_reference_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Reference type 'Device' does not match expected type 'Organization'."
            ),
        ):
            Patient.model_validate(
                {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "1234567890",
                        }
                    ],
                    "generalPractitioner": [
                        {
                            "type": "Device",
                            "identifier": {
                                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                                "value": "A12345",
                            },
                        }
                    ],
                }
            )


class TestGeneralPractitioner:
    def test_expected_reference_type(self) -> None:
        assert GeneralPractitioner._expected_reference_type == "Organization", (
            "_expected_reference_type should be 'Organization'"
        )

    def test_organization_identifier_expected_system(self) -> None:
        assert (
            OrganizationIdentifier._expected_system
            == "https://fhir.nhs.uk/Id/ods-organization-code"
        ), "_expected_system should be the ODS organization code URI"


class TestDevice:
    def test_create_with_asid_identifier(self) -> None:
        device = Device.create(
            identifier=[
                ASIDIdentifier(
                    system="https://fhir.nhs.uk/Id/nhsSpineASID",
                    value="123456789012",
                )
            ],
        )

        assert device.resource_type == "Device", "resource_type should be 'Device'"
        assert device.identifier[0].value == "123456789012", (
            "identifier value should match"
        )

    def test_asid_identifier_expected_system(self) -> None:
        assert ASIDIdentifier._expected_system == (
            "https://fhir.nhs.uk/Id/nhsSpineASID"
        ), "_expected_system should be the ASID URI"


class TestDeviceModelValidate:
    def test_valid_device(self) -> None:
        device = Device.model_validate(
            {
                "resourceType": "Device",
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                        "value": "123456789012",
                    }
                ],
            }
        )

        assert device.identifier[0].value == "123456789012", (
            "identifier value should be parsed"
        )

    def test_wrong_resource_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Patient' does not match expected resource type "
                "'Device'."
            ),
        ):
            Device.model_validate(
                {
                    "resourceType": "Patient",
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/nhsSpineASID",
                            "value": "123",
                        }
                    ],
                }
            )

    def test_empty_identifier_list_fails(self) -> None:
        with pytest.raises(ValidationError, match="too_short"):
            Device.model_validate({"resourceType": "Device", "identifier": []})

    def test_missing_identifier_fails(self) -> None:
        with pytest.raises(ValidationError, match="identifier"):
            Device.model_validate({"resourceType": "Device"})

    @pytest.mark.xfail(
        reason=(
            "The system for the JWT device is not yet defined. Validation should be "
            "added once this is known. [GPCAPIM-358]"
        )
    )
    def test_invalid_identifier_system_fails(self) -> None:
        with pytest.raises(ValidationError, match="does not match expected system"):
            Device.model_validate(
                {
                    "resourceType": "Device",
                    "identifier": [{"system": "https://bad.system", "value": "123"}],
                }
            )


class TestEndpoint:
    def test_create_with_address(self) -> None:
        endpoint = Endpoint.create(address="https://example.com/fhir")

        assert endpoint.resource_type == "Endpoint", (
            "resource_type should be 'Endpoint'"
        )
        assert endpoint.address == "https://example.com/fhir", (
            "address should match the provided URL"
        )

    def test_create_without_address(self) -> None:
        endpoint = Endpoint.create()

        assert endpoint.address is None, "address should default to None"


class TestPractitioner:
    def test_create(self) -> None:
        practitioner = Practitioner.create(
            id="practitioner-1",
            name=[HumanName(family="Smith", given=["Alex"], prefix=["Dr"])],
            identifier=[
                SDSUserIDIdentifier(
                    system="https://fhir.nhs.uk/Id/sds-user-id",
                    value="1234567890",
                ),
                SDSRoleProfileIDIdentifier(
                    system="https://fhir.nhs.uk/Id/sds-role-profile-id",
                    value="R8010:G8000:1001",
                ),
                AgnosticUserRoleIdentifier(system="https://custom.system", value="UR1"),
            ],
        )

        assert practitioner.resource_type == "Practitioner", (
            "resource_type should be 'Practitioner'"
        )
        assert practitioner.id == "practitioner-1", "id should be set"
        assert practitioner.name[0].family == "Smith", "family name should be set"
        assert practitioner.name[0].given == ["Alex"], "given names should be set"
        assert practitioner.identifier[0].system == (
            "https://fhir.nhs.uk/Id/sds-user-id"
        ), "first identifier should be SDS user ID"
        assert practitioner.identifier[1].system == (
            "https://fhir.nhs.uk/Id/sds-role-profile-id"
        ), "second identifier should be SDS role profile ID"
        assert practitioner.identifier[2].system == "https://custom.system", (
            "agnostic identifier should keep provided system"
        )


class TestPractitionerModelValidate:
    def test_valid_practitioner(self) -> None:
        practitioner = Practitioner.model_validate(
            {
                "resourceType": "Practitioner",
                "id": "practitioner-2",
                "name": [{"family": "Jones", "given": ["Sam"], "prefix": ["Mx"]}],
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/sds-user-id",
                        "value": "1234567890",
                    },
                    {
                        "system": "https://fhir.nhs.uk/Id/sds-role-profile-id",
                        "value": "R8010:G8000:1001",
                    },
                    {"system": "https://another.system", "value": "UR-22"},
                ],
            }
        )

        assert practitioner.name[0].family == "Jones", "family should be parsed"
        assert isinstance(practitioner.identifier[0], SDSUserIDIdentifier), (
            "first identifier should be parsed as SDSUserIDIdentifier"
        )
        assert isinstance(practitioner.identifier[1], SDSRoleProfileIDIdentifier), (
            "second identifier should be parsed as SDSRoleProfileIDIdentifier"
        )
        assert isinstance(practitioner.identifier[2], AgnosticUserRoleIdentifier), (
            "third identifier should be parsed as AgnosticUserRoleIdentifier"
        )

    def test_wrong_resource_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Patient' does not match expected resource type "
                "'Practitioner'."
            ),
        ):
            Practitioner.model_validate(
                {
                    "resourceType": "Patient",
                    "id": "practitioner-3",
                    "name": [{"family": "Jones"}],
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/sds-user-id",
                            "value": "123",
                        }
                    ],
                }
            )

    def test_missing_name_fails(self) -> None:
        with pytest.raises(ValidationError, match="name"):
            Practitioner.model_validate(
                {
                    "resourceType": "Practitioner",
                    "id": "practitioner-4",
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/sds-user-id",
                            "value": "123",
                        }
                    ],
                }
            )

    def test_empty_name_list_fails(self) -> None:
        with pytest.raises(ValidationError, match="too_short"):
            Practitioner.model_validate(
                {
                    "resourceType": "Practitioner",
                    "id": "practitioner-5",
                    "name": [],
                    "identifier": [
                        {
                            "system": "https://fhir.nhs.uk/Id/sds-user-id",
                            "value": "123",
                        }
                    ],
                }
            )

    def test_missing_identifier_fails(self) -> None:
        with pytest.raises(ValidationError, match="identifier"):
            Practitioner.model_validate(
                {
                    "resourceType": "Practitioner",
                    "id": "practitioner-6",
                    "name": [{"family": "Jones"}],
                }
            )

    def test_empty_identifier_list_fails(self) -> None:
        with pytest.raises(ValidationError, match="too_short"):
            Practitioner.model_validate(
                {
                    "resourceType": "Practitioner",
                    "id": "practitioner-7",
                    "name": [{"family": "Jones"}],
                    "identifier": [],
                }
            )

    def test_unknown_identifier_system_is_parsed_as_agnostic_identifier(self) -> None:
        practitioner = Practitioner.model_validate(
            {
                "resourceType": "Practitioner",
                "id": "practitioner-8",
                "name": [{"family": "Jones"}],
                "identifier": [
                    {
                        "system": "https://example.org/invalid",
                        "value": "123",
                    }
                ],
            }
        )

        assert isinstance(practitioner.identifier[0], AgnosticUserRoleIdentifier), (
            "unknown systems should be parsed as AgnosticUserRoleIdentifier"
        )


class TestEndpointModelValidate:
    def test_valid_endpoint(self) -> None:
        endpoint = Endpoint.model_validate(
            {"resourceType": "Endpoint", "address": "https://example.com/fhir"}
        )

        assert endpoint.address == "https://example.com/fhir", (
            "address should be parsed from dict"
        )

    def test_valid_endpoint_without_address(self) -> None:
        endpoint = Endpoint.model_validate({"resourceType": "Endpoint"})

        assert endpoint.address is None, "address should default to None"

    def test_wrong_resource_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Bundle' does not match expected resource type "
                "'Endpoint'."
            ),
        ):
            Endpoint.model_validate({"resourceType": "Bundle"})


class TestOrganization:
    def test_create(self) -> None:
        organization = Organization.create(
            name="Leeds Teaching Hospitals NHS Trust",
            identifier=[
                OrganizationIdentifier(
                    value="RR8",
                )
            ],
        )

        assert organization.resource_type == "Organization", (
            "resource_type should be 'Organization'"
        )
        assert organization.name == "Leeds Teaching Hospitals NHS Trust", (
            "name should match the provided organization name"
        )
        assert len(organization.identifier) == 1, "should have one identifier"
        assert organization.identifier[0].system == (
            "https://fhir.nhs.uk/Id/ods-organization-code"
        ), "identifier system should be the ODS organization code URI"
        assert organization.identifier[0].value == "RR8", (
            "identifier value should match the provided ODS code"
        )

    def test_model_validate_with_no_name_raises_error(self) -> None:
        with pytest.raises(ValidationError):
            Organization.model_validate(
                {
                    "resourceType": "Organization",
                    "identifier": [
                        {
                            "system": "https://example.org/invalid",
                            "value": "RR8",
                        }
                    ],
                }
            )

    def test_model_validate_with_invalid_identifier_system_raises_error(self) -> None:
        with pytest.raises(ValidationError, match="does not match expected system"):
            Organization.model_validate(
                {
                    "resourceType": "Organization",
                    "name": "Leeds Teaching Hospitals NHS Trust",
                    "identifier": [
                        {
                            "system": "https://example.org/invalid",
                            "value": "RR8",
                        }
                    ],
                }
            )


class TestBundleModelValidate:
    def test_valid_bundle(self) -> None:
        bundle = Bundle.model_validate(
            {
                "resourceType": "Bundle",
                "type": "searchset",
                "entry": [
                    {
                        "fullUrl": "https://example.com/Patient/1",
                        "resource": {
                            "resourceType": "Patient",
                            "identifier": [
                                {
                                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                                    "value": "1234567890",
                                }
                            ],
                        },
                    }
                ],
            }
        )

        assert bundle.bundle_type == "searchset", (
            "bundle_type should be parsed from JSON"
        )
        assert bundle.entries is not None, "entries should not be None"
        assert len(bundle.entries) == 1, "should have one entry"
        assert isinstance(bundle.entries[0].resource, Patient), (
            "entry resource should be deserialized as Patient"
        )

    def test_valid_bundle_without_entries(self) -> None:
        bundle = Bundle.model_validate({"resourceType": "Bundle", "type": "collection"})

        assert bundle.bundle_type == "collection", "bundle_type should be 'collection'"
        assert bundle.entries is None, "entries should default to None"

    def test_missing_type_fails(self) -> None:
        with pytest.raises(ValidationError, match="type"):
            Bundle.model_validate({"resourceType": "Bundle"})

    def test_wrong_resource_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Endpoint' does not match expected resource type "
                "'Bundle'."
            ),
        ):
            Bundle.model_validate({"resourceType": "Endpoint", "type": "document"})

    def test_entry_missing_full_url_fails(self) -> None:
        with pytest.raises(ValidationError, match="fullUrl"):
            Bundle.model_validate(
                {
                    "resourceType": "Bundle",
                    "type": "document",
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "Patient",
                                "identifier": [
                                    {
                                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                                        "value": "123",
                                    }
                                ],
                            }
                        }
                    ],
                }
            )

    def test_entry_missing_resource_fails(self) -> None:
        with pytest.raises(ValidationError, match="resource"):
            Bundle.model_validate(
                {
                    "resourceType": "Bundle",
                    "type": "document",
                    "entry": [{"fullUrl": "https://example.com"}],
                }
            )


class TestBundleEmpty:
    @pytest.mark.parametrize(
        "bundle_type",
        ["document", "transaction", "searchset", "collection"],
    )
    def test_empty_bundle_types(self, bundle_type: str) -> None:
        bundle = Bundle.empty(bundle_type)  # type: ignore[arg-type]

        assert bundle.bundle_type == bundle_type, (
            f"bundle_type should be '{bundle_type}'"
        )
        assert bundle.entries is None, "entries should be None for empty bundles"
        assert bundle.identifier is None, "identifier should be None for empty bundles"
