import json
from typing import TYPE_CHECKING

from fhir import OperationOutcome, Parameters
from fhir.operation_outcome import OperationOutcomeIssue
from flask.wrappers import Request, Response

from gateway_api.common.common import FlaskResponse

if TYPE_CHECKING:
    from fhir.bundle import Bundle


class RequestValidationError(Exception):
    """Exception raised for errors in the request validation."""


class GetStructuredRecordRequest:
    INTERACTION_ID: str = "urn:nhs:names:services:gpconnect:gpc.getstructuredrecord-1"
    RESOURCE: str = "patient"
    FHIR_OPERATION: str = "$gpc.getstructuredrecord"

    def __init__(self, request: Request) -> None:
        self._http_request = request
        self._headers = request.headers
        self._request_body: Parameters = request.get_json()
        self._response_body: Bundle | OperationOutcome | None = None
        self._status_code: int | None = None

        # Validate required headers
        self._validate_headers()

    @property
    def trace_id(self) -> str:
        trace_id: str = self._headers["Ssp-TraceID"]
        return trace_id

    @property
    def nhs_number(self) -> str:
        nhs_number: str = self._request_body["parameter"][0]["valueIdentifier"]["value"]
        return nhs_number

    @property
    def ods_from(self) -> str:
        ods_from: str = self._headers["ODS-from"]
        return ods_from

    @property
    def request_body(self) -> str:
        return json.dumps(self._request_body)

    def _validate_headers(self) -> None:
        """Validate required headers are present and non-empty.

        :raises RequestValidationError: If required headers are missing or empty.
        """
        trace_id = self._headers.get("Ssp-TraceID", "").strip()
        if not trace_id:
            raise RequestValidationError(
                'Missing or empty required header "Ssp-TraceID"'
            )

        ods_from = self._headers.get("ODS-from", "").strip()
        if not ods_from:
            raise RequestValidationError('Missing or empty required header "ODS-from"')

    def build_response(self) -> Response:
        return Response(
            response=json.dumps(self._response_body),
            status=self._status_code,
            mimetype="application/fhir+json",
        )

    def set_negative_response(self, error: str, status_code: int = 500) -> None:
        self._status_code = status_code
        self._response_body = OperationOutcome(
            resourceType="OperationOutcome",
            issue=[
                OperationOutcomeIssue(
                    severity="error",
                    code="exception",
                    diagnostics=error,
                )
            ],
        )

    def set_response_from_flaskresponse(self, flask_response: FlaskResponse) -> None:
        if flask_response.data:
            self._status_code = flask_response.status_code
            try:
                self._response_body = json.loads(flask_response.data)
            except json.JSONDecodeError as err:
                self.set_negative_response(f"Failed to decode response body: {err}")
            except Exception as err:
                self.set_negative_response(
                    f"Unexpected error decoding response body: {err}"
                )
        else:
            self.set_negative_response(
                error="No response body received",
                status_code=flask_response.status_code,
            )
