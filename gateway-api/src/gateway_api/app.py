import logging
import os
import traceback

from flask import Flask, Request, request
from flask.wrappers import Response

from gateway_api.common.error import AbstractCDGError, UnexpectedError
from gateway_api.controller import Controller
from gateway_api.get_structured_record import (
    GetStructuredRecordRequest,
    GetStructuredRecordResponse,
)

app = Flask(__name__)
app.logger.setLevel("INFO")
logging.basicConfig(level=logging.INFO)


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


def log_request_received(request: Request) -> None:
    log_details = {
        "description": "Received request",
        "method": request.method,
        "path": request.path,
        "headers": dict(request.headers),
    }
    app.logger.info(log_details)


def log_error(error: AbstractCDGError) -> None:
    log_details = {
        "description": "An error occurred",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    app.logger.error(log_details)


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Response:
    log_request_received(request)
    response = GetStructuredRecordResponse()
    response.mirror_headers(request)
    try:
        get_structured_record_request = GetStructuredRecordRequest(request)
        controller = Controller()
        provider_response = controller.run(request=get_structured_record_request)
        response.add_provider_response(provider_response)
    except AbstractCDGError as e:
        log_error(e)
        response.add_error_response(e)
    except Exception:
        error = UnexpectedError(traceback=traceback.format_exc())
        log_error(error)
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
