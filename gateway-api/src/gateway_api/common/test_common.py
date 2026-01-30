"""
Unit tests for :mod:`gateway_api.common.common`.
"""

import pytest

from gateway_api.common import common


@pytest.mark.parametrize(
    ("nhs_number", "expected"),
    [
        ("9434765919", True),  # Just a number
        ("943 476 5919", True),  # Spaces are permitted
        ("987-654-3210", True),  # Hyphens are permitted
        (9434765919, True),  # Integer input is permitted
        ("", False),  # Empty string is invalid
        ("943476591", False),  # 9 digits
        ("94347659190", False),  # 11 digits
        ("9434765918", False),  # wrong check digit
        ("NOT_A_NUMBER", False),  # non-numeric
        ("943SOME_LETTERS4765919", False),  # non-numeric in a valid NHS number
    ],
)
def test_validate_nhs_number(nhs_number: str | int, expected: bool) -> None:
    """
    Validate that separators (spaces, hyphens) are ignored and valid numbers pass.
    """
    assert common.validate_nhs_number(nhs_number) is expected


@pytest.mark.parametrize(
    ("nhs_number", "expected"),
    [
        # All zeros => weighted sum 0 => remainder 0 => check 11 => mapped to 0 => valid
        ("0000000000", True),
        # First 9 digits produce remainder 1 => check 10 => invalid
        ("0000000060", False),
    ],
)
def test_validate_nhs_number_check_edge_cases_10_and_11(
    nhs_number: str | int, expected: bool
) -> None:
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
    assert common.validate_nhs_number(nhs_number) is expected
