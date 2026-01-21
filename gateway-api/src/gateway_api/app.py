import os
from typing import TypedDict

from flask import Flask, request
from flask.wrappers import Response

from gateway_api.get_structed_record import (
    GetStructuredRecordHandler,
    GetStructuredRecordRequest,
)

app = Flask(__name__)


class HealthCheckResponse(TypedDict):
    status: str


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Response:
    get_structured_record_request = GetStructuredRecordRequest(request)
    GetStructuredRecordHandler.handle(get_structured_record_request)
    return get_structured_record_request.build_response()


@app.route("/health", methods=["GET"])
def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT")
    if host is None:
        raise RuntimeError("FLASK_HOST environment variable is not set.")
    if port is None:
        raise RuntimeError("FLASK_PORT environment variable is not set.")
    app.run(host=host, port=int(port))
