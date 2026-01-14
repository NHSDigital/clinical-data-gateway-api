import os
from typing import Any, TypedDict

from flask import Flask, request

from gateway_api.handler import User, greet

app = Flask(__name__)


class APIMResponse[T](TypedDict):
    """A API Management response including a body with a generic type."""

    statusCode: int
    headers: dict[str, str]
    body: T


@app.route("/2015-03-31/functions/function/invocations", methods=["POST"])
def greet_endpoint() -> APIMResponse[str | dict[str, str]]:
    """Greet endpoint that replicates the lambda handler functionality."""
    data = request.get_json(force=True)
    if "payload" not in data:
        return _with_default_headers(status_code=400, body="Name is required")

    name = data["payload"]
    if not name:
        return _with_default_headers(status_code=400, body="Name cannot be empty")
    user = User(name=name)

    try:
        return _with_default_headers(status_code=200, body=f"{greet(user)}")
    except ValueError:
        return _with_default_headers(
            status_code=404, body=f"Provided name cannot be found. name={name}"
        )


def _with_default_headers[T](status_code: int, body: T) -> APIMResponse[T]:
    return APIMResponse(
        statusCode=status_code, headers={"Content-Type": "application/json"}, body=body
    )


@app.route("/health", methods=["GET"])
def health_check() -> APIMResponse[dict[str, Any]]:
    """Health check endpoint."""
    return _with_default_headers(status_code=200, body={"status": "healthy"})


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST")
    if host is None:
        raise RuntimeError("FLASK_HOST environment variable is not set.")
    app.run(host=host, port=8080)
