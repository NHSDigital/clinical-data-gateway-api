"""
Unit tests for :mod:`gateway_api.clinical_jwt.device`.
"""

from gateway_api.clinical_jwt import Device


def test_device_creation_with_all_required_fields() -> None:
    """
    Test that a Device instance can be created with all required fields.
    """
    device = Device(
        system="https://consumersupplier.com/Id/device-identifier",
        value="CONS-APP-4",
        model="Consumer product name",
        version="5.3.0",
    )

    assert device.system == "https://consumersupplier.com/Id/device-identifier"
    assert device.value == "CONS-APP-4"
    assert device.model == "Consumer product name"
    assert device.version == "5.3.0"


def test_device_json_property_returns_valid_json_structure() -> None:
    """
    Test that the json property returns a valid JSON structure for requesting_device.
    """
    device = Device(
        system="https://consumersupplier.com/Id/device-identifier",
        value="CONS-APP-4",
        model="Consumer product name",
        version="5.3.0",
    )

    json_output = device.json

    expected_json = """"requesting_device": {
            "resourceType": "Device",
        "identifier": [
            {
                "system": "https://consumersupplier.com/Id/device-identifier",
            "value": "CONS-APP-4"
            }
        ],
        "model": "Consumer product name",
        "version": "5.3.0"
        }"""

    assert json_output == expected_json


def test_device_str_returns_json() -> None:
    """
    Test that __str__ returns the same value as the json property.
    """
    device = Device(
        system="https://test.com/device",
        value="TEST-001",
        model="Test Model",
        version="1.0.0",
    )

    assert str(device) == device.json
