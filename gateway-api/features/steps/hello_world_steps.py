"""Step definitions for Gateway API hello world feature."""

from behave import given, then, when


@given("the API is running")
def step_api_is_running(context):
    """Verify the API test client is available.

    Args:
        context: Behave context with client from environment.py
    """
    assert context.client is not None
    assert context.app is not None


@when('I send a GET request to "{endpoint}"')
def step_send_get_request(context, endpoint):
    """Send a GET request to the specified endpoint.

    Args:
        context: Behave context
        endpoint: The API endpoint path to request
    """
    context.response = context.client.get(endpoint)


@then("the response status code should be {expected_status:d}")
def step_check_status_code(context, expected_status):
    """Verify the response status code matches expected value.

    Args:
        context: Behave context containing the response
        expected_status: Expected HTTP status code
    """
    assert context.response.status_code == expected_status, (
        f"Expected status {expected_status}, got {context.response.status_code}"
    )


@then('the response should contain "{expected_text}"')
def step_check_response_contains(context, expected_text):
    """Verify the response contains the expected text.

    Args:
        context: Behave context containing the response
        expected_text: Text that should be in the response
    """
    assert expected_text in context.response.text, (
        f"Expected '{expected_text}' in response, got: {context.response.text}"
    )
