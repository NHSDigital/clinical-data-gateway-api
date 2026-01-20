"""Step definitions for Gateway API hello world feature."""

import json
from datetime import timedelta

import requests
from fhir.bundle import Bundle
from fhir.parameters import Parameters
from pytest_bdd import given, parsers, then, when

from tests.acceptance.conftest import ResponseContext
from tests.conftest import Client


@given("the API is running new")
def check_api_is_running(client: Client) -> None:
    response = client.send_health_check()
    assert response.status_code == 200


@when("I send a valid Parameters resource to the endpoint")
def send_get_request(
    client: Client,
    response_context: ResponseContext,
    simple_request_payload: Parameters,
) -> None:
    response_context.response = client.send_to_get_structured_record_endpoint(
        json.dumps(simple_request_payload)
    )


@when("I send a valid Parameters resource to a nonexistent endpoint")
def send_to_nonexistent_endpoint(
    client: Client,
    response_context: ResponseContext,
    simple_request_payload: Parameters,
) -> None:
    nonexistent_endpoint = f"{client.base_url}/nonexistent"
    response_context.response = requests.post(
        url=nonexistent_endpoint,
        data=json.dumps(simple_request_payload),
        timeout=timedelta(seconds=1).total_seconds(),
    )


@then(
    parsers.cfparse(
        "the response status code should be {expected_status:d}",
        extra_types={"expected_status": int},
    )
)
def check_status_code(response_context: ResponseContext, expected_status: int) -> None:
    assert response_context.response is not None, "Response has not been set."
    assert response_context.response.status_code == expected_status, (
        f"Expected status {expected_status}, "
        f"got {response_context.response.status_code}"
    )


@then("the response should contain a valid Bundle resource")
def check_response_contains(
    response_context: ResponseContext, expected_response_payload: Bundle
) -> None:
    """Verify the response contains the expected text.

    Args:
        context: Behave context containing the response
        expected_text: Text that should be in the response
    """
    assert response_context.response, "Response has not been set."
    assert response_context.response.json() == expected_response_payload, (
        "Expected response payload does not match actual response payload."
    )
