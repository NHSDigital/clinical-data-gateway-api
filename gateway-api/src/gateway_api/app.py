import os
from typing import TypedDict

from fhir import Bundle
from flask import Flask, request

from gateway_api.get_structed_record.handler import GetStructuredRecordHandler
from gateway_api.get_structed_record.request import GetStructuredRecordRequest

app = Flask(__name__)


class HealthCheckResponse(TypedDict):
    status: str


@app.route("/patient/$gpc.getstructuredrecord", methods=["POST"])
def get_structured_record() -> Bundle:
    get_structured_record_request = GetStructuredRecordRequest(request)
    response = GetStructuredRecordHandler.handle(get_structured_record_request)
    return response


@app.route("/health", methods=["GET"])
def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST")
    if host is None:
        raise RuntimeError("FLASK_HOST environment variable is not set.")
    app.run(host=host, port=8080)
