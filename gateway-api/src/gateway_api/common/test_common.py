# tests/test_common.py

import pytest

from gateway_api.common import common


@pytest.mark.parametrize(
    "value",
    [
        "9434765919",
        "943 476 5919",  # spaces allowed (non-digits stripped)
        9434765919,  # int input supported
    ],
)
def test_validate_nhs_number_valid(value: str) -> None:
    assert common.validate_nhs_number(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",  # empty
        "123",  # too short
        "12345678901",  # too long
        "abc",  # no digits after stripping
    ],
)
def test_validate_nhs_number_invalid_length_or_non_numeric(value: str) -> None:
    assert common.validate_nhs_number(value) is False
