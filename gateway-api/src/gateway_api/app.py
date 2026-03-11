import os
import traceback

from flask import Flask, request
from flask.wrappers import Response

from gateway_api.common.error import AbstractCDGError, UnexpectedError
from gateway_api.controller import Controller
from gateway_api.get_structured_record import (
    GetStructuredRecordRequest,
)
from gateway_api.get_structured_record.response import GetStructuredRecordResponse

app = Flask(__name__)


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
    response = GetStructuredRecordResponse()
    response.mirror_headers(request)
    try:
        get_structured_record_request = GetStructuredRecordRequest(request)
        controller = Controller()
        provider_response = controller.run(request=get_structured_record_request)
        response.add_provider_response(provider_response)
    except AbstractCDGError as e:
        e.log()
        response.add_error_response(e)
    except Exception:
        error = UnexpectedError(traceback=traceback.format_exc())
        error.log()
        response.add_error_response(error)

    return response.build()


@app.route("/health", methods=["GET"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    version: str = "unknown"

    commit_version: str | None = os.getenv("COMMIT_VERSION")
    build_date: str | None = os.getenv("BUILD_DATE")
    if commit_version and build_date:
        version = f"{build_date}.{commit_version}"

    return {"status": "healthy", "version": version}


if __name__ == "__main__":
    host, port = get_app_host(), get_app_port()
    print(f"Version: {os.getenv('COMMIT_VERSION')}")
    app.run(host=host, port=port)
