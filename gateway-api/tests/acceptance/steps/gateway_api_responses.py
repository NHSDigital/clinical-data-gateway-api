"""Step definitions for Gateway API response behaviour feature."""

import json

from fhir.parameters import Parameters
from pytest_bdd import given, parsers, then, when
from stubs.data.bundles import Bundles

from tests.acceptance.conftest import ResponseContext
from tests.conftest import Client


def _assert_response_status(
    response_context: ResponseContext,
    expected_status: int,
) -> None:
    assert response_context.response is not None, "Response has not been set."
    assert response_context.response.status_code == expected_status, (
        f"Expected status {expected_status}, "
        f"got {response_context.response.status_code}: {response_context.response.text}"
    )


@given("the API is running")
def check_api_is_running(client: Client) -> None:
    response = client.send_health_check()
    assert response.status_code == 200, (
        f"Health check failed with {response.status_code}: {response.text}"
    )


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
    response_context.response = client.send_post_to_path(
        path="/nonexistent",
        payload=json.dumps(simple_request_payload),
    )


@then(
    parsers.cfparse(
        "the response status code should be {expected_status:d}",
        extra_types={"expected_status": int},
    )
)
def check_status_code(response_context: ResponseContext, expected_status: int) -> None:
    _assert_response_status(response_context, expected_status)


@then("the response should be successful")
def check_response_successful(response_context: ResponseContext) -> None:
    _assert_response_status(response_context, 200)


@then("the response should indicate the endpoint was not found")
def check_response_not_found(response_context: ResponseContext) -> None:
    _assert_response_status(response_context, 404)


@then("the response should include the patient's record from the provider")
def check_response_matches_provider(response_context: ResponseContext) -> None:
    assert response_context.response is not None, "Response has not been set."
    assert response_context.response.json() == Bundles.ALICE_JONES_9999999999, (
        "Expected response payload does not match actual response payload."
    )
