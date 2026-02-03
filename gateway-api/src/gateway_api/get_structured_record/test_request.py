import json
from typing import TYPE_CHECKING, cast

import pytest
from fhir.parameters import Parameters
from flask import Request
from werkzeug.test import EnvironBuilder

from gateway_api.common.common import FlaskResponse
from gateway_api.get_structured_record import RequestValidationError
from gateway_api.get_structured_record.request import GetStructuredRecordRequest

if TYPE_CHECKING:
    from fhir.bundle import Bundle


def create_mock_request(headers: dict[str, str], body: Parameters) -> Request:
    """Create a proper Flask Request object with headers and JSON body."""
    builder = EnvironBuilder(
        method="POST",
        path="/patient/$gpc.getstructuredrecord",
        data=json.dumps(body),
        content_type="application/fhir+json",
        headers=headers,
    )
    env = builder.get_environ()
    return Request(env)


@pytest.fixture
def mock_request_with_headers(valid_simple_request_payload: Parameters) -> Request:
    headers = {
        "Ssp-TraceID": "test-trace-id",
        "ODS-from": "test-ods",
    }
    return create_mock_request(headers, valid_simple_request_payload)


class TestGetStructuredRecordRequest:
    def test_trace_id_is_pulled_from_ssp_traceid_header(
        self, mock_request_with_headers: Request
    ) -> None:
        get_structured_record_request = GetStructuredRecordRequest(
            request=mock_request_with_headers
        )

        actual = get_structured_record_request.trace_id
        expected = "test-trace-id"
        assert actual == expected

    def test_ods_is_pulled_from_ssp_from_header(
        self, mock_request_with_headers: Request
    ) -> None:
        get_structured_record_request = GetStructuredRecordRequest(
            request=mock_request_with_headers
        )

        actual = get_structured_record_request.ods_from
        expected = "test-ods"
        assert actual == expected

    def test_nhs_number_is_pulled_from_request_body(
        self, mock_request_with_headers: Request
    ) -> None:
        get_structured_record_request = GetStructuredRecordRequest(
            request=mock_request_with_headers
        )

        actual = get_structured_record_request.nhs_number
        expected = "9999999999"
        assert actual == expected

    def test_nhs_number_is_pulled_from_request_body(
        self, mock_request_with_headers: Request
    ) -> None:
        get_structured_record_request = GetStructuredRecordRequest(
            request=mock_request_with_headers
        )

        actual = get_structured_record_request.nhs_number
        expected = "9999999999"
        assert actual == expected
