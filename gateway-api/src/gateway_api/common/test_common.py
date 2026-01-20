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


def test_validate_nhs_number_returns_false_for_non_ten_digits_and_non_numeric() -> None:
    """
    validate_nhs_number should return False when:
    - The number of digits is not exactly 10.
    - The input is not numeric.

    Notes:
    - The implementation strips non-digit characters before validation, so a fully
        non-numeric input becomes an empty digit string and is rejected.
    """
    # Not ten digits after stripping -> False
    assert common.validate_nhs_number("123456789") is False
    assert common.validate_nhs_number("12345678901") is False

    # Not numeric -> False (becomes 0 digits after stripping)
    assert common.validate_nhs_number("NOT_A_NUMBER") is False


def test_validate_nhs_number_check_edge_cases_10_and_11() -> None:
    """
    validate_nhs_number should behave correctly when the computed ``check`` value
    is 10 or 11.

    - If ``check`` computes to 11, it should be treated as 0, so a number with check
        digit 0 should validate successfully.
    - If ``check`` computes to 10, the number is invalid and validation should return
        False.
    """
    # All zeros => weighted sum 0 => remainder 0 => check 11 => mapped to 0 => valid
    # with check digit 0
    assert common.validate_nhs_number("0000000000") is True

    # First nine digits produce remainder 1 => check 10 => invalid regardless of
    # final digit
    # Choose d9=6 and others 0: total = 6*2 = 12 => 12 % 11 = 1 => check = 10
    assert common.validate_nhs_number("0000000060") is False
