import datetime
import json
from typing import Any

import pytest
from pydantic import BaseModel

from fhir.r4 import Bundle, Patient
from fhir.resources.resource import Meta, Resource


class TestMeta:
    def test_create(self) -> None:
        meta = Meta(
            version_id="1",
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z"),
        )
        assert meta.version_id == "1", "version_id should be set to '1'"
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        ), "last_updated should match the provided datetime"

    def test_create_without_last_updated(self) -> None:
        meta = Meta(version_id="2")

        assert meta.version_id == "2", "version_id should be set to '2'"
        assert meta.last_updated is None, "last_updated should default to None"

    def test_create_without_version(self) -> None:
        meta = Meta(
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        )

        assert meta.version_id is None, "version_id should default to None"
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        ), "last_updated should match the provided datetime"

    def test_create_with_defaults(self) -> None:
        meta = Meta()

        assert meta.version_id is None, "version_id should default to None"
        assert meta.last_updated is None, "last_updated should default to None"

    def test_with_last_updated(self) -> None:
        last_updated = datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        meta = Meta.with_last_updated(last_updated)

        assert meta.last_updated == last_updated, (
            "last_updated should match the provided datetime"
        )
        assert meta.version_id is None, "version_id should default to None"

    def test_with_last_updated_defaults_to_now(self) -> None:
        before_create = datetime.datetime.now(tz=datetime.timezone.utc)
        meta = Meta.with_last_updated(None)
        after_create = datetime.datetime.now(tz=datetime.timezone.utc)

        assert meta.last_updated is not None, "last_updated should not be None"
        assert meta.version_id is None, "version_id should default to None"

        assert before_create <= meta.last_updated, (
            "last_updated should be >= the time before creation"
        )
        assert meta.last_updated <= after_create, (
            "last_updated should be <= the time after creation"
        )

    def test_is_frozen(self) -> None:
        meta = Meta(version_id="1")

        with pytest.raises(AttributeError):
            meta.version_id = "2"  # type: ignore[misc]


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


class TestResourceInitSubclass:
    def test_subclass_without_resource_type_raises(self) -> None:
        with pytest.raises(TypeError):

            class _Bad(Resource):
                pass


class TestResourceCreate:
    def test_create_sets_resource_type(self) -> None:
        patient = Patient.create(
            identifier=[Patient.PatientIdentifier.from_nhs_number("1234567890")]
        )

        assert patient.resource_type == "Patient", "resource_type should be 'Patient'"

    def test_create_on_bundle(self) -> None:
        bundle = Bundle.create(type="document", entry=None)

        assert bundle.resource_type == "Bundle", "resource_type should be 'Bundle'"


class TestResourceModelDump:
    def test_model_dump_excludes_none(self) -> None:
        patient = Patient.create(
            identifier=[Patient.PatientIdentifier.from_nhs_number("1234567890")]
        )
        dumped = patient.model_dump()

        assert "generalPractitioner" not in dumped, (
            "None fields should be excluded from model_dump"
        )
        assert "meta" not in dumped, "None meta should be excluded from model_dump"

    def test_model_dump_json_excludes_none(self) -> None:
        patient = Patient.create(
            identifier=[Patient.PatientIdentifier.from_nhs_number("1234567890")]
        )
        payload = json.loads(patient.model_dump_json())

        assert "generalPractitioner" not in payload, (
            "None fields should be excluded from model_dump_json"
        )
        assert "meta" not in payload, "None meta should be excluded"
