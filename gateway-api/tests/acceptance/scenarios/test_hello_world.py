"""
Provides the scenario bindings for the hello world feature file.
"""

from pytest_bdd import scenario

from tests.acceptance.steps.hello_world_steps import *  # noqa: F403,S2208 - Required to import all hello world steps.


@scenario("hello_world.feature", "Get hello world message")
def test_hello_world() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass


@scenario("hello_world.feature", "Accessing a non-existent endpoint returns a 404")
def test_nonexistent_route() -> None:
    # No body required here as this method simply provides a binding to the BDD step
    pass
