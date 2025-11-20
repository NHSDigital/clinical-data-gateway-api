from typing import TypedDict

from gateway_api.handler import User, greet


class LambdaResponse[T](TypedDict):
    """A lambda response including a body with a generic type."""

    statusCode: int
    headers: dict[str, str]
    body: T


def _with_default_headers[T](status_code: int, body: T) -> LambdaResponse[T]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": body,
    }


def handler(event: dict[str, str], context: dict[str, str]) -> LambdaResponse[str]:
    print(f"Received event: {event}")

    if "payload" not in event:
        return _with_default_headers(status_code=400, body="Name is required")

    name = event["payload"]
    if not name:
        return _with_default_headers(status_code=400, body="Name cannot be empty")
    user = User(name=name)

    try:
        return _with_default_headers(status_code=200, body=f"{greet(user)}")
    except ValueError:
        return _with_default_headers(
            status_code=404, body=f"Provided name cannot be found. name={name}"
        )
