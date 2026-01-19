import os
from typing import TypedDict

from fhir import Bundle
from flask import Flask, request
from flask.wrappers import Response

from gateway_api.get_structured_record import (
    GetStructuredRecordHandler,
    GetStructuredRecordRequest,
)

app = Flask(__name__)


class HealthCheckResponse(TypedDict):
    status: str
    version: str


def get_app_host() -> str:
    host = os.getenv("FLASK_HOST")
    if host is None:
        raise RuntimeError("FLASK_HOST environment variable is not set.")
    print(f"Starting Flask app on host: {host}")
    return host


def get_app_port() -> int:
    port = os.getenv("FLASK_PORT")
    if port is None:
        raise RuntimeError("FLASK_PORT environment variable is not set.")
    print(f"Starting Flask app on port: {port}")
    return int(port)


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Response:
    try:
        get_structured_record_request = GetStructuredRecordRequest(request)
        GetStructuredRecordHandler.handle(get_structured_record_request)
    except Exception as e:
        get_structured_record_request.set_negative_response(str(e))
    return get_structured_record_request.build_response()


@app.route("/health", methods=["GET"])
def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    version: str = "unkonwn"

    commit_version: str | None = os.getenv("COMMIT_VERSION")
    build_date: str | None = os.getenv("BUILD_DATE")
    if commit_version and build_date:
        version = f"{build_date}.{commit_version}"

    return {"status": "healthy", "version": version}


if __name__ == "__main__":
    host, port = get_app_host(), get_app_port()
    print(f"Version: {os.getenv('COMMIT_VERSION')}")
    app.run(host=host, port=port)
