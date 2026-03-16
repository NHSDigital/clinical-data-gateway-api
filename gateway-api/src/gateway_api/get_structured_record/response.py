import json
from collections.abc import Mapping
from typing import ClassVar

from flask import Request, Response
from requests import Response as HTTPResponse
from requests.structures import CaseInsensitiveDict

from gateway_api.common.error import AbstractCDGError


class GetStructuredRecordResponse:
    MIME_TYPE: ClassVar[str] = "application/fhir+json"

    def __init__(self) -> None:
        self._response_body: str | None = None
        self._headers: Mapping[str, str] | None = None
        self._status_code: int | None = None

    def mirror_headers(self, request: Request) -> None:
        self._headers = CaseInsensitiveDict(request.headers)

    @property
    def headers(self) -> Mapping[str, str] | None:
        return self._headers

    def add_provider_response(self, provider_response: HTTPResponse) -> None:
        self._response_body = json.dumps(provider_response.json())
        self._status_code = provider_response.status_code

    def add_error_response(self, error: AbstractCDGError) -> None:
        self._response_body = error.operation_outcome.model_dump_json()
        self._status_code = error.status_code

    def build(self) -> Response:
        return Response(
            response=self._response_body,
            status=self._status_code,
            mimetype=self.MIME_TYPE,
        )
