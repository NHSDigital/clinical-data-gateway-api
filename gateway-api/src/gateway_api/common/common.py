"""
Shared lightweight types and helpers used across the gateway API.
"""

import re
from dataclasses import dataclass

# This project uses JSON request/response bodies as strings in the controller layer.
# The alias is used to make intent clearer in function signatures.
type json_str = str


@dataclass
class FlaskResponse:
    """
    Lightweight response container returned by controller entry points.

    This mirrors the minimal set of fields used by the surrounding web framework.

    :param status_code: HTTP status code for the response (e.g., 200, 400, 404).
    :param data: Response body as text, if any.
    :param headers: Response headers, if any.
    """

    # TODO: Un-ai all these docstrings

    status_code: int
    data: str | None = None
    headers: dict[str, str] | None = None


def validate_nhs_number(value: str | int) -> bool:
    """
    Validate an NHS number using the NHS modulus-11 check digit algorithm.

    The input may be a string or integer. Any non-digit separators in string
    inputs (spaces, hyphens, etc.) are ignored.

    :param value: NHS number as a string or integer. Non-digit characters
        are ignored when a string is provided.
    :returns: ``True`` if the number is a valid NHS number, otherwise ``False``.
    """
    str_value = str(value)  # Just in case they passed an integer
    digits = re.sub(r"\D", "", str_value or "")

    if len(digits) != 10:
        return False
    if not digits.isdigit():
        return False

    first_nine = [int(ch) for ch in digits[:9]]
    provided_check_digit = int(digits[9])

    weights = list(range(10, 1, -1))
    total = sum(d * w for d, w in zip(first_nine, weights, strict=True))

    remainder = total % 11
    check = 11 - remainder

    if check == 11:
        check = 0
    if check == 10:
        return False  # invalid NHS number

    return check == provided_check_digit
