"""
Unit tests for :mod:`gateway_api.common.common`.
"""

from gateway_api.common import common


def test_validate_nhs_number_accepts_valid_number_with_separators() -> None:
    """
    Validate that separators (spaces, hyphens) are ignored and valid numbers pass.
    """
    assert common.validate_nhs_number("943 476 5919") is True
    assert common.validate_nhs_number("943-476-5919") is True
    assert common.validate_nhs_number(9434765919) is True


def test_validate_nhs_number_rejects_wrong_length_and_bad_check_digit() -> None:
    """Validate that incorrect lengths and invalid check digits are rejected."""
    assert common.validate_nhs_number("") is False
    assert common.validate_nhs_number("943476591") is False  # 9 digits
    assert common.validate_nhs_number("94347659190") is False  # 11 digits
    assert common.validate_nhs_number("9434765918") is False  # wrong check digit
