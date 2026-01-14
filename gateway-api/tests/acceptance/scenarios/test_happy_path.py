"""
Provides the scenario bindings for the hello world feature file.
"""

from pytest_bdd import scenario

from tests.acceptance.steps.happy_path import *  # noqa: F403,S2208 - Required to import all happy path steps.


@scenario("happy_path.feature", "Get structured record request")
def test_structured_record_request() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass


@scenario("happy_path.feature", "Accessing a non-existent endpoint returns a 404")
def test_nonexistent_route() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass
