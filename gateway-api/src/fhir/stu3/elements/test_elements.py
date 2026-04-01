import pytest
from pydantic import ValidationError

from fhir.stu3 import Issue, IssueCode, IssueSeverity, Parameters, PatientIdentifier


class TestParameters:
    def test_create(self) -> None:
        """Test creating a Parameters resource."""
        parameter = Parameters.Parameter(
            valueIdentifier=PatientIdentifier(
                value="9000000009",
            ),
        )

        params = Parameters.create(parameter=[parameter])

        assert params.resource_type == "Parameters", (
            "resourceType should be 'Parameters'"
        )
        assert len(params.parameter) == 1, "parameter list should contain one entry"
        assert params.parameter[0] == parameter, (
            "first parameter should match the provided Parameter"
        )

    def test_create_with_multiple_parameters(self) -> None:
        """Test creating a Parameters resource with multiple parameters."""
        param_a = Parameters.Parameter(
            valueIdentifier=PatientIdentifier(
                value="9000000009",
            ),
        )
        param_b = Parameters.Parameter(
            valueIdentifier=PatientIdentifier(
                value="9000000017",
            ),
        )

        params = Parameters.create(parameter=[param_a, param_b])

        assert len(params.parameter) == 2, "parameter list should contain two entries"
        assert params.parameter[0].valueIdentifier.value == "9000000009", (
            "first parameter NHS number should be '9000000009'"
        )
        assert params.parameter[1].valueIdentifier.value == "9000000017", (
            "second parameter NHS number should be '9000000017'"
        )

    def test_model_validate_valid(self) -> None:
        """Test model_validate with valid Parameters JSON."""
        params = Parameters.model_validate(
            {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "valueIdentifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9000000009",
                        },
                    }
                ],
            }
        )

        assert params.resource_type == "Parameters", (
            "resourceType should be 'Parameters'"
        )
        assert len(params.parameter) == 1, "parameter list should contain one entry"
        assert params.parameter[0].valueIdentifier.value == "9000000009", (
            "valueIdentifier value should be '9000000009'"
        )
        assert params.parameter[0].valueIdentifier.system == (
            "https://fhir.nhs.uk/Id/nhs-number"
        ), "valueIdentifier system should be the NHS number URI"

    def test_model_validate_with_wrong_resource_type_raises_error(self) -> None:
        """Test that an incorrect resourceType is rejected."""
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Patient' does not match expected resource type "
                "'Parameters'."
            ),
        ):
            Parameters.model_validate(
                {
                    "resourceType": "Patient",
                    "parameter": [
                        {
                            "valueIdentifier": {
                                "system": "https://fhir.nhs.uk/Id/nhs-number",
                                "value": "9000000009",
                            },
                        }
                    ],
                }
            )

    def test_model_validate_with_invalid_identifier_system_raises_error(self) -> None:
        """Test that an invalid identifier system is rejected."""
        with pytest.raises(
            ValidationError,
            match=(
                "Identifier system 'https://example.org/invalid' does not match "
                "expected system 'https://fhir.nhs.uk/Id/nhs-number'."
            ),
        ):
            Parameters.model_validate(
                {
                    "resourceType": "Parameters",
                    "parameter": [
                        {
                            "valueIdentifier": {
                                "system": "https://example.org/invalid",
                                "value": "9000000009",
                            },
                        }
                    ],
                }
            )

    def test_model_validate_missing_parameter_raises_error(self) -> None:
        """Test that missing parameter field is rejected."""
        with pytest.raises(ValidationError):
            Parameters.model_validate(
                {
                    "resourceType": "Parameters",
                }
            )

    def test_model_validate_empty_parameter_list(self) -> None:
        """Test creating Parameters with an empty parameter list."""
        with pytest.raises(ValidationError):
            Parameters.model_validate(
                {
                    "resourceType": "Parameters",
                    "parameter": [],
                }
            )

    def test_model_dump_json_roundtrip(self) -> None:
        """Test JSON serialization roundtrip preserves data."""
        params = Parameters.create(
            parameter=[
                Parameters.Parameter(
                    valueIdentifier=PatientIdentifier(
                        value="9000000009",
                    ),
                )
            ],
        )

        json_str = params.model_dump_json()

        assert '"resourceType":"Parameters"' in json_str.replace(" ", ""), (
            "JSON output should contain the resourceType"
        )
        assert "9000000009" in json_str, (
            "JSON output should contain the NHS number value"
        )

    def test_is_frozen(self) -> None:
        """Test that Parameters fields are frozen (immutable)."""
        params = Parameters.create(
            parameter=[
                Parameters.Parameter(
                    valueIdentifier=PatientIdentifier(
                        value="9000000009",
                    ),
                )
            ],
        )

        with pytest.raises((ValidationError, AttributeError)):
            params.parameter = []


class TestParameter:
    def test_create(self) -> None:
        """Test creating a Parameter element."""
        identifier = PatientIdentifier(
            value="9000000009",
        )
        parameter = Parameters.Parameter(valueIdentifier=identifier)

        assert parameter.valueIdentifier == identifier, (
            "valueIdentifier should match the provided identifier"
        )
        assert parameter.valueIdentifier.value == "9000000009", (
            "valueIdentifier value should be '9000000009'"
        )
        assert parameter.valueIdentifier.system == (
            "https://fhir.nhs.uk/Id/nhs-number"
        ), "valueIdentifier system should be the NHS number URI"

    def test_is_frozen(self) -> None:
        """Test that Parameter fields are frozen (immutable)."""
        parameter = Parameters.Parameter(
            valueIdentifier=PatientIdentifier(
                value="9000000009",
            ),
        )

        with pytest.raises(AttributeError):
            parameter.valueIdentifier = PatientIdentifier(  # type: ignore[misc]
                value="0000000000",
            )


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
