from pytest_bdd import scenario

from .steps.hello_world_steps import *  # noqa: F403 - Required to import all hello world steps.


@scenario("hello_world.feature", "Get hello world message")
def test_hello_world() -> None:
    pass


@scenario("hello_world.feature", "Accessing a non-existent endpoint returns a 404")
def test_nonexistent_route() -> None:
    pass
