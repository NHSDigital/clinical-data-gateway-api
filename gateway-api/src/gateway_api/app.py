import os
import traceback
from collections.abc import Callable
from logging import basicConfig, getLogger

from flask import Flask, Request, request
from flask.wrappers import Response

from gateway_api.common.error import AbstractCDGError, UnexpectedError
from gateway_api.controller import Controller
from gateway_api.get_structured_record import (
    GetStructuredRecordRequest,
    GetStructuredRecordResponse,
)

app = Flask(__name__)
_logger = getLogger(__name__)


def start_app(app: Flask) -> None:
    setup_logging()
    log_env_vars()
    configure_app(app)
    log_starting_app(app)
    app.run(host=app.config["FLASK_HOST"], port=app.config["FLASK_PORT"])


def setup_logging() -> None:
    basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
    )


def configure_app(app: Flask) -> None:
    config = {
        "FLASK_HOST": get_env_var("FLASK_HOST", str),
        "FLASK_PORT": get_env_var("FLASK_PORT", int),
        "PDS_URL": get_env_var("PDS_URL", str),
        "SDS_URL": get_env_var("SDS_URL", str),
        "SDS_API_TOKEN": get_env_var("SDS_API_TOKEN", str),
    }
    app.config.update(config)


def get_env_var[T](name: str, parser: Callable[[str], T]) -> T:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"{name} environment variable is not set.")
    try:
        return parser(value)
    except Exception as e:
        raise RuntimeError(f"Error loading {name} environment variable: {e}") from e


def log_request_received(request: Request) -> None:
    sanitized_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() != "authorization"
    }
    log_details = {
        "description": "Received request",
        "method": request.method,
        "path": request.path,
        "headers": sanitized_headers,
    }
    _logger.info(log_details)


def log_error(error: AbstractCDGError) -> None:
    log_details = {
        "description": "An error occurred",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }
    _logger.error(log_details)


def log_env_vars() -> None:
    env_vars = {
        key: value
        for key, value in os.environ.items()
        if key in {"FLASK_HOST", "FLASK_PORT", "PDS_URL", "SDS_URL"}
    }
    log_details = {
        "description": "Initializing Flask app",
        "env_vars": env_vars,
    }
    _logger.info(log_details)


def log_starting_app(app: Flask) -> None:
    log_details = {
        "description": "Starting Flask app",
        "host": app.config["FLASK_HOST"],
        "port": app.config["FLASK_PORT"],
        "pds_base_url": app.config["PDS_URL"],
        "sds_base_url": app.config["SDS_URL"],
    }
    _logger.info(log_details)


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Response:
    log_request_received(request)
    response = GetStructuredRecordResponse()
    response.mirror_headers(request)
    try:
        get_structured_record_request = GetStructuredRecordRequest(request)
        controller = Controller(
            pds_base_url=app.config["PDS_URL"],
            sds_base_url=app.config["SDS_URL"],
            sds_api_key=app.config["SDS_API_TOKEN"],
        )
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
    start_app(app)
