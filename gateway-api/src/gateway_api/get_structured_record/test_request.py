import pytest
from fhir.parameters import Parameters
from flask import Request

from gateway_api.get_structured_record.request import GetStructuredRecordRequest


class MockRequest:
    def __init__(self, headers: dict[str, str], body: Parameters) -> None:
        self.headers = headers
        self.body = body

    def get_json(self) -> Parameters:
        return self.body


@pytest.fixture
def mock_request_with_headers(valid_simple_request_payload: Parameters) -> MockRequest:
    headers = {
        "Ssp-TraceID": "test-trace-id",
        "ODS-from": "test-ods",
    }
    return MockRequest(headers, valid_simple_request_payload)


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
