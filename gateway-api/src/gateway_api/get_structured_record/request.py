import json
from typing import TYPE_CHECKING

from fhir import OperationOutcome, Parameters
from fhir.operation_outcome import OperationOutcomeIssue
from flask.wrappers import Request, Response
from werkzeug.exceptions import BadRequest

from gateway_api.common.common import FlaskResponse
from gateway_api.common.error import InvalidRequestJSONError, MissingOrEmptyHeaderError

if TYPE_CHECKING:
    from fhir.bundle import Bundle

# Access record structured interaction ID from
# https://developer.nhs.uk/apis/gpconnect/accessrecord_structured_development.html#spine-interactions
ACCESS_RECORD_STRUCTURED_INTERACTION_ID = (
    "urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1"
)


class GetStructuredRecordRequest:
    INTERACTION_ID: str = ACCESS_RECORD_STRUCTURED_INTERACTION_ID
    RESOURCE: str = "patient"
    FHIR_OPERATION: str = "$gpc.getstructuredrecord"

    def __init__(self, request: Request) -> None:
        self._http_request = request
        self._headers = request.headers
        try:
            self._request_body: Parameters = request.get_json()
        except BadRequest as error:
            raise InvalidRequestJSONError() from error

        self._response_body: Bundle | OperationOutcome | None = None
        self._status_code: int | None = None

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
        trace_id = self._headers.get("Ssp-TraceID", "").strip()
        if not trace_id:
            raise MissingOrEmptyHeaderError(header="Ssp-TraceID")

        ods_from = self._headers.get("ODS-from", "").strip()
        if not ods_from:
            raise MissingOrEmptyHeaderError(header="ODS-from")

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
