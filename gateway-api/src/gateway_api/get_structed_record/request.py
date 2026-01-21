from typing import TYPE_CHECKING

from flask.wrappers import Request

if TYPE_CHECKING:
    from fhir import Parameters


class GetStructuredRecordRequest:
    interaction_id: str = "urn:nhs:names:services:gpconnect:gpc.getstructuredrecord-1"
    resource: str = "patient"
    fhir_operation: str = "$gpc.getstructuredrecord"

    def __init__(self, request: Request) -> None:
        self._http_request = request
        self._headers = request.headers
        self._request_body: Parameters = request.get_json()

    @property
    def trace_id(self) -> str:
        trace_id: str = self._headers["Ssp-TraceID"]
        return trace_id

    @property
    def nhs_number(self) -> str:
        nhs_number: str = self._request_body["parameter"][0]["valueIdentifier"]["value"]
        return nhs_number

    @property
    def consumer_asid(self) -> str:
        consumer_asid: str = self._headers["Ssp-from"]
        return consumer_asid

    @property
    def provider_asid(self) -> str:
        provider_asid: str = self._headers["Ssp-to"]
        return provider_asid
