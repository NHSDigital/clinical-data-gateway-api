import os
from typing import TypedDict

from fhir import Bundle
from flask import Flask, request

from gateway_api.get_structed_record.handler import GetStructuredRecordHandler
from gateway_api.get_structed_record.request import GetStructuredRecordRequest
from gateway_api.handler import User, greet

app = Flask(__name__)


class APIMResponse[T](TypedDict):
    """A API Management response including a body with a generic type."""

    statusCode: int
    headers: dict[str, str]
    body: T


class HealthCheckResponse(TypedDict):
    status: str


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Bundle:
    """Endpoint to get structured record, replicating lambda handler functionality."""
    get_structured_record_request = GetStructuredRecordRequest(request)
    response = GetStructuredRecordHandler.handle(get_structured_record_request)
    return response


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
def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST")
    if host is None:
        raise RuntimeError("FLASK_HOST environment variable is not set.")
    app.run(host=host, port=8080)
