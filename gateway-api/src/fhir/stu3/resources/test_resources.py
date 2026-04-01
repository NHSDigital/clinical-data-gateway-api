import pytest
from pydantic import ValidationError

from fhir.stu3 import Issue, IssueCode, IssueSeverity, OperationOutcome


class TestOperationOutcome:
    def test_create(self) -> None:
        class _TestIssue(Issue):
            pass

        outcome = OperationOutcome.create(
            issue=[
                _TestIssue(
                    severity=IssueSeverity.ERROR,
                    code=IssueCode.INVALID,
                    diagnostics="Something failed",
                )
            ],
        )

        assert outcome.resource_type == "OperationOutcome", (
            "resource_type should be 'OperationOutcome'"
        )
        assert len(outcome.issue) == 1, "should have one issue"
        assert outcome.issue[0].severity == IssueSeverity.ERROR, (
            "issue severity should be ERROR"
        )
        assert outcome.issue[0].code == IssueCode.INVALID, (
            "issue code should be INVALID"
        )
        assert outcome.issue[0].diagnostics == "Something failed", (
            "diagnostics should match"
        )


class TestOperationOutcomeModelValidate:
    def test_valid_operation_outcome(self) -> None:
        outcome = OperationOutcome.model_validate(
            {
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "invalid",
                        "diagnostics": "Bad request",
                    }
                ],
            }
        )

        assert outcome.issue[0].severity == IssueSeverity.ERROR, (
            "severity should be parsed"
        )
        assert outcome.issue[0].code == IssueCode.INVALID, "code should be parsed"
        assert outcome.issue[0].diagnostics == "Bad request", (
            "diagnostics should be parsed"
        )

    def test_missing_issue_fails(self) -> None:
        with pytest.raises(ValidationError, match="issue"):
            OperationOutcome.model_validate({"resourceType": "OperationOutcome"})

    def test_wrong_resource_type_fails(self) -> None:
        with pytest.raises(
            ValidationError,
            match=(
                "Resource type 'Patient' does not match expected resource type "
                "'OperationOutcome'."
            ),
        ):
            OperationOutcome.model_validate(
                {
                    "resourceType": "Patient",
                    "issue": [{"severity": "error", "code": "invalid"}],
                }
            )
