"""
Unit tests for :mod:`gateway_api.clinical_jwt.practitioner`.
"""

from json import loads

from gateway_api.clinical_jwt import Practitioner


def test_practitioner_creation_with_all_fields() -> None:
    """
    Test that a Practitioner instance can be created with all fields.
    """
    practitioner = Practitioner(
        id="10019",
        sds_userid="111222333444",
        role_profile_id="444555666777",
        userid_url="https://consumersupplier.com/Id/user-guid",
        userid_value="98ed4f78-814d-4266-8d5b-cde742f3093c",
        family_name="Doe",
        given_name="John",
        prefix="Mr",
    )

    assert practitioner.id == "10019"
    assert practitioner.sds_userid == "111222333444"
    assert practitioner.role_profile_id == "444555666777"
    assert practitioner.userid_url == "https://consumersupplier.com/Id/user-guid"
    assert practitioner.userid_value == "98ed4f78-814d-4266-8d5b-cde742f3093c"
    assert practitioner.family_name == "Doe"
    assert practitioner.given_name == "John"
    assert practitioner.prefix == "Mr"


def test_practitioner_json_property_returns_valid_structure() -> None:
    """
    Test that the json property returns a valid JSON structure for
    requesting_practitioner.
    """
    input_practitioner = Practitioner(
        id="10019",
        sds_userid="111222333444",
        role_profile_id="444555666777",
        userid_url="https://consumersupplier.com/Id/user-guid",
        userid_value="98ed4f78-814d-4266-8d5b-cde742f3093c",
        family_name="Doe",
        given_name="John",
        prefix="Mr",
    )

    json_output = input_practitioner.json
    jdict = loads(json_output)
    output_practitioner = Practitioner(
        id=jdict["id"],
        sds_userid=jdict["identifier"][0]["value"],
        role_profile_id=jdict["identifier"][1]["value"],
        userid_url=jdict["identifier"][2]["system"],
        userid_value=jdict["identifier"][2]["value"],
        family_name=jdict["name"][0]["family"],
        given_name=jdict["name"][0].get("given", [None])[0],
        prefix=jdict["name"][0].get("prefix", [None])[0],
    )

    assert input_practitioner == output_practitioner


def test_practitioner_str_returns_json() -> None:
    """
    Test that __str__ returns the same value as the json property.
    """
    practitioner = Practitioner(
        id="10026",
        sds_userid="888999000111",
        role_profile_id="111222333444",
        userid_url="https://test.com/user",
        userid_value="test-guid-7",
        family_name="Taylor",
    )

    assert str(practitioner) == practitioner.json


def test_practitioner_identifier_systems() -> None:
    """
    Test that the correct identifier systems are used in the JSON output.
    """
    practitioner = Practitioner(
        id="10027",
        sds_userid="999000111222",
        role_profile_id="222333444555",
        userid_url="https://test.com/user",
        userid_value="test-guid-8",
        family_name="Anderson",
    )

    json_output = practitioner.json

    # Verify the correct system URLs are used
    assert "https://fhir.nhs.uk/Id/sds-user-id" in json_output
    assert "https://fhir.nhs.uk/Id/sds-role-profile-id" in json_output
