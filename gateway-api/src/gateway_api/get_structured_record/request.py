from collections.abc import Mapping
from typing import ClassVar

from fhir.stu3 import Parameters
from flask.wrappers import Request
from pydantic import ValidationError
from requests.structures import CaseInsensitiveDict
from werkzeug.exceptions import BadRequest

from gateway_api.common.error import (
    InvalidRequestJSONError,
    MissingOrEmptyHeaderError,
)

# Access record structured interaction ID from
# https://developer.nhs.uk/apis/gpconnect/accessrecord_structured_development.html#spine-interactions
ACCESS_RECORD_STRUCTURED_INTERACTION_ID = (
    "urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1"
)

# The SDS Sandbox environment only returns results for this interaction ID.
# Non-sandbox environments should use ACCESS_RECORD_STRUCTURED_INTERACTION_ID.
# TODO: Remove this once we no longer support sandbox (probably in GPCAPIM-396).
SDS_SANDBOX_INTERACTION_ID = "urn:nhs:names:services:psis:REPC_IN150016UK05"


class GetStructuredRecordRequest:
    INTERACTION_ID: ClassVar[str] = ACCESS_RECORD_STRUCTURED_INTERACTION_ID
    RESOURCE: ClassVar[str] = "patient"
    FHIR_OPERATION: ClassVar[str] = "$gpc.getstructuredrecord"

    def __init__(self, request: Request) -> None:
        self._http_request = request
        self._headers = CaseInsensitiveDict(request.headers)
        try:
            self.parameters = Parameters.model_validate(request.get_json())
        except (BadRequest, ValidationError) as error:
            raise InvalidRequestJSONError() from error

        self._status_code: int | None = None

        self._validate_headers()

    @property
    def trace_id(self) -> str:
        trace_id: str = self._headers["Ssp-TraceID"]
        return trace_id

    @property
    def nhs_number(self) -> str:
        nhs_number = self.parameters.parameter[0].valueIdentifier.value
        return nhs_number

    @property
    def ods_from(self) -> str:
        ods_from: str = self._headers["ODS-from"]
        return ods_from

    @property
    def request_body(self) -> str:
        return self.parameters.model_dump_json()

    @property
    def headers(self) -> Mapping[str, str]:
        return self._headers

    def _validate_headers(self) -> None:
        trace_id = self._headers.get("Ssp-TraceID", "").strip()
        if not trace_id:
            raise MissingOrEmptyHeaderError(header="Ssp-TraceID")

        ods_from = self._headers.get("ODS-from", "").strip()
        if not ods_from:
            raise MissingOrEmptyHeaderError(header="ODS-from")
