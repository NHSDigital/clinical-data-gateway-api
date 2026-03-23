"""Provides scenario bindings for the gateway API responses feature file."""

from pytest_bdd import scenario

from tests.acceptance.steps.gateway_api_responses import *  # noqa: F403,S2208 - Required to import all response steps.


@scenario(
    "gateway_api_responses.feature",
    "Valid structured record request returns the expected patient record",
)
def test_structured_record_request() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass


@scenario(
    "gateway_api_responses.feature",
    "Valid structured record request to a non-existent endpoint returns an endpoint not"
    " found error",
)
def test_nonexistent_route() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass
