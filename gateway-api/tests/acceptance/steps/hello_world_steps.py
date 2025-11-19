"""Step definitions for Gateway API hello world feature."""

from pytest_bdd import given, parsers, then, when

from tests.acceptance.conftest import ResponseContext
from tests.conftest import Client


@given("the API is running")
def step_api_is_running(client: Client) -> None:
    """Verify the API test client is available.

    Args:
        client: Test client from conftest.py
    """
    response = client.send("test")
    assert response.text is not None
    assert response.status_code == 200


@when(parsers.cfparse('I send "{message}" to the endpoint'))
def step_send_get_request(
    client: Client, message: str, response_context: ResponseContext
) -> None:
    """Send a GET request to the specified endpoint.

    Args:
        client: Test client
        endpoint: The API endpoint path to request
    """
    response_context.response = client.send(message)


# fmt: off
@then(parsers.cfparse("the response status code should be {expected_status:d}",extra_types={"expected_status": int}))  # noqa: E501 - BDD steps must be declared on a singular line.
# fmt: on
def step_check_status_code(
    response_context: ResponseContext, expected_status: int
) -> None:
    """Verify the response status code matches expected value.

    Args:
        context: Behave context containing the response
        expected_status: Expected HTTP status code
    """
    assert response_context.response, "Response has not been set."

    data = response_context.response.json()

    assert data["statusCode"] == expected_status, (
        f"Expected status {expected_status}, "
        f"got {response_context.response.status_code}"
    )


@then(parsers.cfparse('the response should contain "{expected_text}"'))
def step_check_response_contains(
    response_context: ResponseContext, expected_text: str
) -> None:
    """Verify the response contains the expected text.

    Args:
        context: Behave context containing the response
        expected_text: Text that should be in the response
    """
    assert response_context.response, "Response has not been set."

    assert expected_text in response_context.response.text, (
        f"Expected '{expected_text}' in response, got: {response_context.response.text}"
    )
