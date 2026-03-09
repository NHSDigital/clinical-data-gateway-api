"""
Unit tests for :mod:`gateway_api.clinical_jwt.jwt`.
"""

from unittest.mock import Mock, patch

import jwt as pyjwt
import pytest

from gateway_api.clinical_jwt import JWT


def test_jwt_creation_with_required_fields() -> None:
    """
    Test that a JWT instance can be created with all required fields.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
    )

    assert token.issuer == "https://example.com"
    assert token.subject == "user-123"
    assert token.audience == "https://provider.example.com"
    assert token.requesting_device == {"device": "info"}
    assert token.requesting_organization == {"org": "info"}
    assert token.requesting_practitioner == {"practitioner": "info"}
    assert token.algorithm == "none"
    assert token.type == "JWT"
    assert token.reason_for_request == "directcare"
    assert token.requested_scope == "patient/*.read"


@patch("gateway_api.clinical_jwt.jwt.time")
def test_jwt_default_issued_at_and_expiration(mock_time: Mock) -> None:
    """
    Test that issued_at and expiration have correct default values.
    """
    mock_time.return_value = 1000.0

    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
    )

    assert token.issued_at == 1000
    assert token.expiration == 1300  # issued_at + 300


def test_jwt_issue_time_property() -> None:
    """
    Test that issue_time property returns ISO formatted timestamp.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
        issued_at=1609459200,  # 2021-01-01 00:00:00 UTC
    )

    assert token.issue_time == "2021-01-01T00:00:00+00:00"


def test_jwt_exp_time_property() -> None:
    """
    Test that exp_time property returns ISO formatted timestamp.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
        expiration=1609459500,  # 2021-01-01 00:05:00 UTC
    )

    assert token.exp_time == "2021-01-01T00:05:00+00:00"


def test_jwt_payload_contains_all_required_fields() -> None:
    """
    Test that payload() returns a dictionary with all required JWT fields.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
        issued_at=1000,
        expiration=1300,
    )

    payload = token.payload()

    expected = {
        "iss": token.issuer,
        "sub": token.subject,
        "aud": token.audience,
        "exp": token.expiration,
        "iat": token.issued_at,
        "requesting_device": token.requesting_device,
        "requesting_organization": token.requesting_organization,
        "requesting_practitioner": token.requesting_practitioner,
        "reason_for_request": token.reason_for_request,
        "requested_scope": token.requested_scope,
    }

    assert payload == expected


def test_jwt_encode_returns_string() -> None:
    """
    Test that encode() returns a valid JWT token string with correct structure.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
        issued_at=1000,
        expiration=1300,
    )

    encoded = token.encode()

    # Use PyJWT to decode and verify the token structure
    try:
        pyjwt.decode(
            encoded,
            options={"verify_signature": False},  # NOSONAR S5659 (not signed)
        )
    except pyjwt.DecodeError as err:
        pytest.fail(f"Failed to decode JWT: {err}")
    except Exception as err:
        pytest.fail(f"Unexpected error during JWT decoding: {err}")


def test_jwt_decode_reconstructs_token() -> None:
    """
    Test that decode() can reconstruct a JWT from an encoded token string.
    """
    original = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device={"device": "info"},
        requesting_organization={"org": "info"},
        requesting_practitioner={"practitioner": "info"},
        issued_at=1000,
        expiration=1300,
    )

    encoded = original.encode()
    decoded = JWT.decode(encoded)

    assert decoded == original, (
        f"The decoded token, {decoded}, does not match the original, {original}"
    )
