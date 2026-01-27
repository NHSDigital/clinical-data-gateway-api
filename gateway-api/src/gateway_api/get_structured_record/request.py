import json

from fhir import OperationOutcome, Parameters
from fhir.bundle import Bundle
from fhir.operation_outcome import OperationOutcomeIssue
from flask.wrappers import Request, Response


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

    def build_response(self) -> Response:
        return Response(
            response=json.dumps(self._response_body),
            status=self._status_code,
            mimetype="application/fhir+json",
        )

    def set_positive_response(self, bundle: Bundle) -> None:
        self._status_code = 200
        self._response_body = bundle

    def set_negative_response(self, error: str) -> None:
        self._status_code = 500
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
