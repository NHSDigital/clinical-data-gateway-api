import pytest
from pydantic import BaseModel, ValidationError

from fhir.elements.identifier import Identifier


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
