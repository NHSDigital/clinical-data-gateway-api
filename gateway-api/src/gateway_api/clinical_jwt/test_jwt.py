"""
Unit tests for :mod:`gateway_api.clinical_jwt.jwt`.
"""

from unittest.mock import Mock, patch

import jwt as pyjwt

from gateway_api.clinical_jwt import JWT


def test_jwt_creation_with_required_fields() -> None:
    """
    Test that a JWT instance can be created with all required fields.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
    )

    assert token.issuer == "https://example.com"
    assert token.subject == "user-123"
    assert token.audience == "https://provider.example.com"
    assert token.requesting_device == '{"device": "info"}'
    assert token.requesting_organization == "ORG-123"
    assert token.requesting_practitioner == '{"practitioner": "info"}'
    assert token.algorithm is None
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
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
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
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
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
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
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
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
        issued_at=1000,
        expiration=1300,
    )

    payload = token.payload()

    assert payload["iss"] == token.issuer
    assert payload["sub"] == token.subject
    assert payload["aud"] == token.audience
    assert payload["exp"] == token.expiration
    assert payload["iat"] == token.issued_at
    assert payload["requesting_device"] == token.requesting_device
    assert payload["requesting_organization"] == token.requesting_organization
    assert payload["requesting_practitioner"] == token.requesting_practitioner
    assert payload["reason_for_request"] == token.reason_for_request
    assert payload["requested_scope"] == token.requested_scope


def test_jwt_encode_returns_string() -> None:
    """
    Test that encode() returns a valid JWT token string with correct structure.
    """
    token = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
        issued_at=1000,
        expiration=1300,
    )

    encoded = token.encode()

    # Use PyJWT to decode and verify the token structure
    pyjwt.decode(
        encoded,
        options={"verify_signature": False},  # NOSONAR S5659 (not signed)
    )


def test_jwt_decode_reconstructs_token() -> None:
    """
    Test that decode() can reconstruct a JWT from an encoded token string.
    """
    original = JWT(
        issuer="https://example.com",
        subject="user-123",
        audience="https://provider.example.com",
        requesting_device='{"device": "info"}',
        requesting_organization="ORG-123",
        requesting_practitioner='{"practitioner": "info"}',
        issued_at=1000,
        expiration=1300,
    )

    encoded = original.encode()
    decoded = JWT.decode(encoded)

    assert decoded.issuer == original.issuer
    assert decoded.subject == original.subject
    assert decoded.audience == original.audience
    assert decoded.requesting_device == original.requesting_device
    assert decoded.requesting_organization == original.requesting_organization
    assert decoded.requesting_practitioner == original.requesting_practitioner
    assert decoded.issued_at == original.issued_at
    assert decoded.expiration == original.expiration
