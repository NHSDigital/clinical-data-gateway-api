# tests/test_common.py

from gateway_api.common import common


def test_flask_response_defaults() -> None:
    r = common.FlaskResponse(status_code=200)
    assert r.status_code == 200
    assert r.data is None
    assert r.headers is None


def test_validate_nhs_number_accepts_valid_number_with_separators() -> None:
    assert common.validate_nhs_number("943 476 5919") is True
    assert common.validate_nhs_number("943-476-5919") is True
    assert common.validate_nhs_number(9434765919) is True


def test_validate_nhs_number_rejects_wrong_length_and_bad_check_digit() -> None:
    assert common.validate_nhs_number("") is False
    assert common.validate_nhs_number("943476591") is False  # 9 digits
    assert common.validate_nhs_number("94347659190") is False  # 11 digits
    assert common.validate_nhs_number("9434765918") is False  # wrong check digit
