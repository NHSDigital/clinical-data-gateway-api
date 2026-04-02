"""JWT validation for GPConnect FHIR API requests."""

from time import time
from typing import Any

from gateway_api.clinical_jwt import JWT
from gateway_api.common.error import JWTValidationError


class JWTValidator:
    """Validator for JWT claims structure and contents."""

    @staticmethod
    def validate_required_fields(jwt_obj: JWT) -> None:
        """
        Validate that all required JWT fields are present and non-empty.

        Raises:
            JWTValidationError: If any required field is missing or empty.
        """
        missing_fields = []
        if not jwt_obj.issuer:
            missing_fields.append("issuer")
        if not jwt_obj.subject:
            missing_fields.append("subject")
        if not jwt_obj.audience:
            missing_fields.append("audience")
        if not jwt_obj.requesting_device:
            missing_fields.append("requesting_device")
        if not jwt_obj.requesting_organization:
            missing_fields.append("requesting_organization")
        if not jwt_obj.requesting_practitioner:
            missing_fields.append("requesting_practitioner")
        if jwt_obj.issued_at is None:
            missing_fields.append("issued_at")
        if jwt_obj.expiration is None:
            missing_fields.append("expiration")

        if missing_fields:
            field_list = ", ".join(missing_fields)
            raise JWTValidationError(
                error_details=f"JWT missing required fields: {field_list}"
            )

    @staticmethod
    def validate_timestamps(jwt_obj: JWT) -> None:
        """
        Validate JWT timestamp fields are integers and expiration is 5 minutes after
        issued_at.

        Raises:
            JWTValidationError: If timestamps are invalid.
        """
        if not isinstance(jwt_obj.issued_at, int):
            raise JWTValidationError(
                error_details="JWT issued_at must be a unix timestamp (integer)"
            )

        if not isinstance(jwt_obj.expiration, int):
            raise JWTValidationError(
                error_details="JWT expiration must be a unix timestamp (integer)"
            )

        expected_expiration = jwt_obj.issued_at + 300
        if jwt_obj.expiration != expected_expiration:
            raise JWTValidationError(
                error_details=(
                    f"JWT expiration must be exactly 5 minutes (300 seconds) "
                    f"after issued_at. "
                    f"Expected {expected_expiration}, got {jwt_obj.expiration}"
                )
            )

        if jwt_obj.issued_at > time():
            raise JWTValidationError(
                error_details="JWT issued_at cannot be in the future"
            )
        if jwt_obj.expiration < time():
            raise JWTValidationError(error_details="JWT has expired")

    @staticmethod
    def validate_device(device: dict[str, Any]) -> None:
        """
        Validate JWT requesting_device structure.

        Raises:
            JWTValidationError: If device structure is invalid.
        """
        if not hasattr(device, "get"):
            raise JWTValidationError(
                error_details="Invalid requesting_device: must be a dict"
            )

        device_errors = []
        if device.get("resourceType") != "Device":
            device_errors.append("resourceType must be 'Device'")
        if not device.get("identifier") or not isinstance(
            device.get("identifier"), list
        ):
            device_errors.append("Device identifier must be a non-empty list")
        else:
            identifier = device["identifier"][0]
            if not identifier.get("system"):
                device_errors.append("identifier[0].system is required")
            if not identifier.get("value"):
                device_errors.append("identifier[0].value is required")
        if not device.get("model"):
            device_errors.append("model is required")
        if not device.get("version"):
            device_errors.append("version is required")

        if device_errors:
            raise JWTValidationError(
                error_details=f"Invalid requesting_device: {', '.join(device_errors)}"
            )

    @staticmethod
    def validate_organization(org: dict[str, Any]) -> None:
        """
        Validate JWT requesting_organization structure.

        Raises:
            JWTValidationError: If organization structure is invalid.
        """
        if not hasattr(org, "get"):
            raise JWTValidationError(
                error_details="Invalid requesting_organization: must be a dict"
            )

        org_errors = []
        if org.get("resourceType") != "Organization":
            org_errors.append("resourceType must be 'Organization'")
        if not org.get("identifier") or not isinstance(org.get("identifier"), list):
            org_errors.append("Organization identifier must be a non-empty list")
        else:
            identifier = org["identifier"][0]
            if not identifier.get("system"):
                org_errors.append("identifier[0].system is required")
            if not identifier.get("value"):
                org_errors.append("identifier[0].value is required")
        if not org.get("name"):
            org_errors.append("name is required")

        if org_errors:
            raise JWTValidationError(
                error_details=(
                    f"Invalid requesting_organization: {', '.join(org_errors)}"
                )
            )

    @staticmethod
    def _validate_practitioner_identifiers(
        identifiers: list[dict[str, Any]],
    ) -> list[str]:
        """Validate practitioner identifier list structure and contents."""
        errors = []

        for i, identifier in enumerate(identifiers):
            if not identifier.get("system"):
                errors.append(f"identifier[{i}].system is required")
            if not identifier.get("value"):
                errors.append(f"identifier[{i}].value is required")
        return errors

    @staticmethod
    def _validate_practitioner_name(names: list[dict[str, Any]]) -> list[str]:
        """Validate practitioner name list structure and contents."""
        errors = []

        name = names[0]
        if not name.get("family"):
            errors.append("name[0].family is required")
        return errors

    @staticmethod
    def validate_practitioner(pract: dict[str, Any]) -> None:
        """
        Validate JWT requesting_practitioner structure.

        Raises:
            JWTValidationError: If practitioner structure is invalid.
        """
        if not hasattr(pract, "get"):
            raise JWTValidationError(
                error_details="Invalid requesting_practitioner: must be a dict"
            )

        pract_errors = []

        if pract.get("resourceType") != "Practitioner":
            pract_errors.append("resourceType must be 'Practitioner'")

        if not pract.get("id"):
            pract_errors.append("id is required")

        # Validate identifiers
        identifiers = pract.get("identifier")
        if not identifiers or not isinstance(identifiers, list):
            pract_errors.append("Practitioner identifier must be a non-empty list")
        else:
            pract_errors.extend(
                JWTValidator._validate_practitioner_identifiers(identifiers)
            )

        # Validate name
        names = pract.get("name")
        if not names or not isinstance(names, list):
            pract_errors.append("name must be a non-empty list")
        else:
            pract_errors.extend(JWTValidator._validate_practitioner_name(names))

        if pract_errors:
            raise JWTValidationError(
                error_details=(
                    f"Invalid requesting_practitioner: {', '.join(pract_errors)}"
                )
            )

    @staticmethod
    def validate(jwt_obj: JWT) -> None:
        """
        Validate JWT claims structure and contents.

        Collects all validation errors before raising to provide complete feedback.

        Raises:
            JWTValidationError: If validation fails, with all errors listed.
        """
        errors = []

        try:
            JWTValidator.validate_required_fields(jwt_obj)
        except JWTValidationError as e:
            errors.append(str(e))

        try:
            JWTValidator.validate_timestamps(jwt_obj)
        except JWTValidationError as e:
            errors.append(str(e))

        try:
            JWTValidator.validate_device(jwt_obj.requesting_device)
        except JWTValidationError as e:
            errors.append(str(e))

        try:
            JWTValidator.validate_organization(jwt_obj.requesting_organization)
        except JWTValidationError as e:
            errors.append(str(e))

        try:
            JWTValidator.validate_practitioner(jwt_obj.requesting_practitioner)
        except JWTValidationError as e:
            errors.append(str(e))

        if errors:
            raise JWTValidationError(error_details="; ".join(errors))
