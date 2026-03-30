"""Unit tests for JWT validator."""

import pytest

from gateway_api.clinical_jwt import JWT
from gateway_api.clinical_jwt.validator import JWTValidator
from gateway_api.common.error import JWTValidationError


class TestValidateRequiredFields:
    """Tests for validate_required_fields method."""

    def test_valid_jwt_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid JWT passes required fields validation."""
        try:
            JWTValidator.validate_required_fields(valid_jwt)  # Should not raise
        except JWTValidationError as err:
            pytest.fail(f"JWT validation failed: {err}")

    def test_all_missing_fields_reported_in_error(self) -> None:
        """Test that all missing required fields are reported in a single error."""
        jwt = JWT(
            issuer="",
            subject="",
            audience="",
            requesting_device={},
            requesting_organization={},
            requesting_practitioner={},
            issued_at=None,  # type: ignore
            expiration=None,  # type: ignore
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_required_fields(jwt)
        error_message = str(exc_info.value)
        # Verify all required fields are mentioned in the error
        assert "issuer" in error_message
        assert "subject" in error_message
        assert "audience" in error_message
        assert "requesting_device" in error_message
        assert "requesting_organization" in error_message
        assert "requesting_practitioner" in error_message
        assert "issued_at" in error_message
        assert "expiration" in error_message


class TestValidateTimestamps:
    """Tests for validate_timestamps method."""

    def test_valid_timestamps_pass(self, valid_jwt: JWT) -> None:
        """Test that valid timestamps pass validation."""
        JWTValidator.validate_timestamps(valid_jwt)  # Should not raise

    def test_non_integer_issued_at_raises_error(self, valid_jwt: JWT) -> None:
        """Test that non-integer issued_at raises validation error."""
        jwt = JWT(
            issuer=valid_jwt.issuer,
            subject=valid_jwt.subject,
            audience=valid_jwt.audience,
            requesting_device=valid_jwt.requesting_device,
            requesting_organization=valid_jwt.requesting_organization,
            requesting_practitioner=valid_jwt.requesting_practitioner,
            issued_at="not an int",  # type: ignore
            expiration=valid_jwt.expiration,
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_timestamps(jwt)
        assert "issued_at must be a unix timestamp" in str(exc_info.value)

    def test_non_integer_expiration_raises_error(self, valid_jwt: JWT) -> None:
        """Test that non-integer expiration raises validation error."""
        jwt = JWT(
            issuer=valid_jwt.issuer,
            subject=valid_jwt.subject,
            audience=valid_jwt.audience,
            requesting_device=valid_jwt.requesting_device,
            requesting_organization=valid_jwt.requesting_organization,
            requesting_practitioner=valid_jwt.requesting_practitioner,
            issued_at=valid_jwt.issued_at,
            expiration="not an int",  # type: ignore
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_timestamps(jwt)
        assert "expiration must be a unix timestamp" in str(exc_info.value)

    def test_expiration_not_300_seconds_after_issued_at_raises_error(
        self, valid_jwt: JWT
    ) -> None:
        """Test that expiration not exactly 300 seconds after issued_at raises error."""
        jwt = JWT(
            issuer=valid_jwt.issuer,
            subject=valid_jwt.subject,
            audience=valid_jwt.audience,
            requesting_device=valid_jwt.requesting_device,
            requesting_organization=valid_jwt.requesting_organization,
            requesting_practitioner=valid_jwt.requesting_practitioner,
            issued_at=1000000,
            expiration=1000400,  # 400 seconds, not 300
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_timestamps(jwt)
        assert "exactly 5 minutes (300 seconds)" in str(exc_info.value)


class TestValidateDevice:
    """Tests for validate_device method."""

    def test_valid_device_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid device passes validation."""
        JWTValidator.validate_device(valid_jwt.requesting_device)  # Should not raise

    def test_invalid_device_reports_all_errors(self) -> None:
        """Test that all device validation errors are reported."""
        device = {
            "resourceType": "WrongType",
            "identifier": [{"missing": "system_and_value"}],
            # missing model and version
        }
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_device(device)
        error_message = str(exc_info.value)
        assert "resourceType must be 'Device'" in error_message
        assert "identifier[0].system is required" in error_message
        assert "identifier[0].value is required" in error_message
        assert "model is required" in error_message
        assert "version is required" in error_message


class TestValidateOrganization:
    """Tests for validate_organization method."""

    def test_valid_organization_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid organization passes validation."""
        JWTValidator.validate_organization(valid_jwt.requesting_organization)

    def test_invalid_organization_reports_all_errors(self) -> None:
        """Test that all organization validation errors are reported."""
        org = {
            "resourceType": "WrongType",
            "identifier": [{"missing": "system_and_value"}],
            # missing name
        }
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_organization(org)
        error_message = str(exc_info.value)
        assert "resourceType must be 'Organization'" in error_message
        assert "identifier[0].system is required" in error_message
        assert "identifier[0].value is required" in error_message
        assert "name is required" in error_message


class TestValidatePractitioner:
    """Tests for validate_practitioner method."""

    def test_valid_practitioner_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid practitioner passes validation."""
        JWTValidator.validate_practitioner(valid_jwt.requesting_practitioner)

    def test_invalid_practitioner_reports_all_errors(self) -> None:
        """Test that all practitioner validation errors are reported."""
        pract = {
            "resourceType": "WrongType",
            # missing id
            "identifier": [
                {"missing": "system_and_value"},
                {"system": "sys2", "value": "val2"},
                {"system": "sys3", "value": "val3"},
            ],  # 3 items but first missing system/value
            "name": [{"given": ["Test"]}],  # Missing family
        }
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_practitioner(pract)
        error_message = str(exc_info.value)
        assert "resourceType must be 'Practitioner'" in error_message
        assert "id is required" in error_message
        assert "identifier[0].system is required" in error_message
        assert "identifier[0].value is required" in error_message
        assert "family is required" in error_message


class TestValidate:
    """Tests for the main validate method."""

    def test_valid_jwt_passes_all_validation(self, valid_jwt: JWT) -> None:
        """Test that a completely valid JWT passes all validation."""
        JWTValidator.validate(valid_jwt)  # Should not raise

    def test_multiple_validation_errors_collected(self, valid_jwt: JWT) -> None:
        """
        Test that all validation errors from all validators are collected and
        reported together.
        """
        jwt = JWT(
            issuer="",  # Invalid - missing issuer
            subject=valid_jwt.subject,
            audience=valid_jwt.audience,
            requesting_device={
                "resourceType": "Wrong",  # Invalid - wrong resourceType
            },
            requesting_organization={
                "resourceType": "Wrong",  # Invalid - wrong resourceType
            },
            requesting_practitioner={
                "resourceType": "Wrong",  # Invalid - wrong resourceType
            },
            issued_at="not an int",  # type: ignore  # Invalid - not an integer
            expiration=valid_jwt.expiration,
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate(jwt)
        error_message = str(exc_info.value)
        # Should contain errors from all validators
        assert "issuer" in error_message
        assert "timestamp" in error_message or "unix timestamp" in error_message
        assert "Device" in error_message
        assert "Organization" in error_message
        assert "Practitioner" in error_message
