import re
from dataclasses import dataclass


@dataclass
class FlaskResponse:
    status_code: int
    data: str | None = None
    headers: dict[str, str] | None = None


def validate_nhs_number(value: str | int) -> bool:
    # TODO: Un-AI all these docstrings
    """
    Validate an NHS number using the NHS modulus-11 check digit algorithm.

    Algorithm summary:
        - NHS number is 10 digits: d1..d9 + check digit d10
        - Compute: total = d1*10 + d2*9 + ... + d9*2
        - remainder = total % 11
        - check = 11 - remainder
        - If check == 11 => check digit must be 0
        - If check == 10 => check digit must be 10 (impossible as digit) => invalid
        - If remainder == 1 => check would be 10 => invalid
        - Else check digit must match d10
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
