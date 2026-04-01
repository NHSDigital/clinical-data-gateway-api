import uuid

import pytest
from pydantic import BaseModel, ValidationError

from fhir.r4 import (
    Identifier,
    Issue,
    IssueCode,
    IssueSeverity,
    Reference,
    UUIDIdentifier,
)


class TestIdentifierInitSubclass:
    def test_subclass_sets_expected_system(self) -> None:
        class _Custom(Identifier, expected_system="https://example.com"):
            pass

        assert _Custom._expected_system == "https://example.com", (
            "_expected_system should be set by __init_subclass__"
        )

    def test_multiple_subclasses_have_independent_expected_system(self) -> None:
        class _A(Identifier, expected_system="system-a"):
            pass

        class _B(Identifier, expected_system="system-b"):
            pass

        assert _A._expected_system == "system-a", (
            "_A._expected_system should be 'system-a'"
        )
        assert _B._expected_system == "system-b", (
            "_B._expected_system should be 'system-b'"
        )

    def test_subclass_without_expected_system_raises(self) -> None:
        with pytest.raises(TypeError):

            class _Bad(Identifier):  # type: ignore[call-arg]
                pass


class TestIdentifierModelValidate:
    def test_valid_system_passes_validation(self) -> None:
        class _TestId(Identifier, expected_system="https://example.com"):
            pass

        class _Container(BaseModel):
            identifier: _TestId

        result = _Container.model_validate(
            {"identifier": {"system": "https://example.com", "value": "abc-123"}}
        )

        assert result.identifier.system == "https://example.com", (
            "system should match the expected system"
        )
        assert result.identifier.value == "abc-123", "value should be 'abc-123'"

    def test_invalid_system_fails_validation(self) -> None:
        class _TestId(Identifier, expected_system="expected-system"):
            pass

        class _Container(BaseModel):
            identifier: _TestId

        with pytest.raises(
            ValidationError,
            match="Identifier system 'invalid-system' does not match expected "
            "system 'expected-system'.",
        ):
            _Container.model_validate(
                {"identifier": {"system": "invalid-system", "value": "some-value"}}
            )

    def test_missing_value_fails_validation(self) -> None:
        class _TestId(Identifier, expected_system="sys"):
            pass

        class _Container(BaseModel):
            identifier: _TestId

        with pytest.raises(ValidationError):
            _Container.model_validate({"identifier": {"system": "sys"}})

    def test_missing_system_fails_validation(self) -> None:
        class _TestId(Identifier, expected_system="sys"):
            pass

        class _Container(BaseModel):
            identifier: _TestId

        with pytest.raises(ValidationError):
            _Container.model_validate({"identifier": {"value": "v"}})


class TestUUIDIdentifier:
    def test_create_with_value(self) -> None:
        expected_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        identifier = UUIDIdentifier(value=expected_uuid)

        assert identifier.system == "https://tools.ietf.org/html/rfc4122", (
            "system should be the RFC 4122 URI"
        )
        assert identifier.value == str(expected_uuid), (
            "value should match the provided UUID string"
        )

    def test_create_without_value(self) -> None:
        identifier = UUIDIdentifier()

        assert identifier.system == "https://tools.ietf.org/html/rfc4122", (
            "system should be the RFC 4122 URI"
        )
        parsed_uuid = uuid.UUID(identifier.value)
        assert parsed_uuid.version == 4, "auto-generated value should be a UUID v4"

    def test_each_call_generates_unique_uuid(self) -> None:
        a = UUIDIdentifier()
        b = UUIDIdentifier()

        assert a.value != b.value, "two UUIDIdentifiers should have different values"

    def test_expected_system_class_var(self) -> None:
        assert (
            UUIDIdentifier._expected_system == "https://tools.ietf.org/html/rfc4122"
        ), "_expected_system should be set to RFC 4122 URI"


class TestIssue:
    def test_diagnostics_defaults_to_none(self) -> None:
        class _ConcreteIssue(Issue):
            pass

        issue = _ConcreteIssue(severity=IssueSeverity.WARNING, code=IssueCode.EXCEPTION)

        assert issue.diagnostics is None, "diagnostics should default to None"

    def test_is_frozen(self) -> None:
        class _ConcreteIssue(Issue):
            pass

        issue = _ConcreteIssue(severity=IssueSeverity.FATAL, code=IssueCode.EXCEPTION)

        with pytest.raises(AttributeError):
            issue.severity = IssueSeverity.WARNING  # type: ignore[misc]


class TestReferenceInitSubclass:
    def test_subclass_sets_expected_reference_type(self) -> None:
        class _TestId(Identifier, expected_system="sys"):
            pass

        class _TestRef(Reference, reference_type="Patient"):
            identifier: _TestId

        assert _TestRef._expected_reference_type == "Patient", (
            "_expected_reference_type should be 'Patient'"
        )

    def test_multiple_subclasses_have_independent_reference_types(self) -> None:
        class _IdA(Identifier, expected_system="sys-a"):
            pass

        class _IdB(Identifier, expected_system="sys-b"):
            pass

        class _RefA(Reference, reference_type="Patient"):
            identifier: _IdA

        class _RefB(Reference, reference_type="Organization"):
            identifier: _IdB

        assert _RefA._expected_reference_type == "Patient", (
            "_RefA should have reference_type 'Patient'"
        )
        assert _RefB._expected_reference_type == "Organization", (
            "_RefB should have reference_type 'Organization'"
        )

    def test_subclass_without_reference_type_raises(self) -> None:
        with pytest.raises(TypeError):

            class _BadRef(Reference):
                pass


class TestReferenceModelValidate:
    @pytest.fixture
    def id_and_ref_classes(self) -> tuple[type[Identifier], type[Reference]]:
        class _TestId(Identifier, expected_system="https://example.com/id"):
            pass

        class _TestRef(Reference, reference_type="Patient"):
            identifier: _TestId

        return _TestId, _TestRef

    def test_valid_reference(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        result = ref_cls.model_validate(
            {
                "identifier": {
                    "system": "https://example.com/id",
                    "value": "12345",
                },
                "type": "Patient",
            }
        )

        assert result.reference is None, "reference should default to None"
        assert result.display is None, "display should default to None"

    def test_valid_reference_with_optional_fields(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        result = ref_cls.model_validate(
            {
                "identifier": {
                    "system": "https://example.com/id",
                    "value": "12345",
                },
                "type": "Patient",
                "reference": "Patient/12345",
                "display": "Jane Doe",
            }
        )

        assert result.reference == "Patient/12345", (
            "reference should be 'Patient/12345'"
        )
        assert result.display == "Jane Doe", "display should be 'Jane Doe'"

    def test_invalid_reference_type_fails(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        with pytest.raises(
            ValidationError,
            match="Reference type 'Organization' does not match expected "
            "type 'Patient'.",
        ):
            ref_cls.model_validate(
                {
                    "identifier": {
                        "system": "https://example.com/id",
                        "value": "12345",
                    },
                    "type": "Organization",
                }
            )

    def test_invalid_identifier_system_fails(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        with pytest.raises(
            ValidationError,
            match="Identifier system 'wrong-sys' does not match expected "
            "system 'https://example.com/id'.",
        ):
            ref_cls.model_validate(
                {
                    "identifier": {"system": "wrong-sys", "value": "12345"},
                    "type": "Patient",
                }
            )

    def test_missing_type_fails(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        with pytest.raises(ValidationError):
            ref_cls.model_validate(
                {
                    "identifier": {
                        "system": "https://example.com/id",
                        "value": "12345",
                    },
                }
            )

    def test_missing_identifier_fails(
        self, id_and_ref_classes: tuple[type[Identifier], type[Reference]]
    ) -> None:
        _, ref_cls = id_and_ref_classes

        with pytest.raises(ValidationError):
            ref_cls.model_validate({"type": "Patient"})
