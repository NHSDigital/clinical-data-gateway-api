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

    def test_missing_resource_type_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing resourceType raises validation error."""
        device = valid_jwt.requesting_device.copy()
        device["resourceType"] = "WrongType"
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_device(device)
        assert "resourceType must be 'Device'" in str(exc_info.value)

    def test_missing_identifier_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing identifier raises validation error."""
        device = valid_jwt.requesting_device.copy()
        del device["identifier"]
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_device(device)
        assert "identifier must be a non-empty list" in str(exc_info.value)

    def test_missing_model_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing model raises validation error."""
        device = valid_jwt.requesting_device.copy()
        del device["model"]
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_device(device)
        assert "model is required" in str(exc_info.value)


class TestValidateOrganization:
    """Tests for validate_organization method."""

    def test_valid_organization_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid organization passes validation."""
        JWTValidator.validate_organization(valid_jwt.requesting_organization)

    def test_missing_resource_type_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing resourceType raises validation error."""
        org = valid_jwt.requesting_organization.copy()
        org["resourceType"] = "WrongType"
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_organization(org)
        assert "resourceType must be 'Organization'" in str(exc_info.value)

    def test_missing_name_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing name raises validation error."""
        org = valid_jwt.requesting_organization.copy()
        del org["name"]
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_organization(org)
        assert "name is required" in str(exc_info.value)


class TestValidatePractitioner:
    """Tests for validate_practitioner method."""

    def test_valid_practitioner_passes(self, valid_jwt: JWT) -> None:
        """Test that a valid practitioner passes validation."""
        JWTValidator.validate_practitioner(valid_jwt.requesting_practitioner)

    def test_missing_resource_type_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing resourceType raises validation error."""
        pract = valid_jwt.requesting_practitioner.copy()
        pract["resourceType"] = "WrongType"
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_practitioner(pract)
        assert "resourceType must be 'Practitioner'" in str(exc_info.value)

    def test_missing_id_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing id raises validation error."""
        pract = valid_jwt.requesting_practitioner.copy()
        del pract["id"]
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_practitioner(pract)
        assert "id is required" in str(exc_info.value)

    def test_insufficient_identifiers_raises_error(self, valid_jwt: JWT) -> None:
        """Test that less than 3 identifiers raises validation error."""
        pract = valid_jwt.requesting_practitioner.copy()
        pract["identifier"] = [{"system": "sys", "value": "val"}]  # Only 1
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_practitioner(pract)
        assert "at least 3 items" in str(exc_info.value)

    def test_missing_family_name_raises_error(self, valid_jwt: JWT) -> None:
        """Test that missing family name raises validation error."""
        pract = valid_jwt.requesting_practitioner.copy()
        pract["name"] = [{"given": ["Test"]}]  # Missing family
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate_practitioner(pract)
        assert "family is required" in str(exc_info.value)


class TestValidate:
    """Tests for the main validate method."""

    def test_valid_jwt_passes_all_validation(self, valid_jwt: JWT) -> None:
        """Test that a completely valid JWT passes all validation."""
        JWTValidator.validate(valid_jwt)  # Should not raise

    def test_invalid_jwt_reports_all_errors(self, valid_jwt: JWT) -> None:
        """Test that validation reports all errors, not just the first one."""
        jwt = JWT(
            issuer="",  # Invalid - missing required field
            subject=valid_jwt.subject,
            audience=valid_jwt.audience,
            requesting_device={"resourceType": "Wrong"},  # Invalid - wrong resourceType
            requesting_organization=valid_jwt.requesting_organization,
            requesting_practitioner=valid_jwt.requesting_practitioner,
            issued_at=valid_jwt.issued_at,
            expiration=valid_jwt.expiration,
        )
        with pytest.raises(JWTValidationError) as exc_info:
            JWTValidator.validate(jwt)
        error_message = str(exc_info.value)
        # Should contain both the missing issuer error and the device error
        assert "issuer" in error_message
        assert "Device" in error_message or "device" in error_message
