from typing import Any

import pytest
from flask import Request

from gateway_api.common.error import (
    MissingOrEmptyHeaderError,
    UnsupportedMediaTypeError,
)
from gateway_api.conftest import create_mock_request
from gateway_api.get_structured_record.request import GetStructuredRecordRequest


@pytest.fixture
def mock_request_with_headers(valid_simple_request_payload: dict[str, Any]) -> Request:
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

    def test_raises_value_error_when_ods_from_header_is_missing(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """Test that ValueError is raised when ODS-from header is missing."""
        headers = {
            "Ssp-TraceID": "test-trace-id",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            MissingOrEmptyHeaderError,
            match='Missing or empty required header "ODS-from"',
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_ods_from_header_is_whitespace(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """
        Test that ValueError is raised when ODS-from header contains only whitespace.
        """
        headers = {
            "Ssp-TraceID": "test-trace-id",
            "ODS-from": "   ",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            MissingOrEmptyHeaderError,
            match='Missing or empty required header "ODS-from"',
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_trace_id_header_is_missing(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """Test that ValueError is raised when Ssp-TraceID header is missing."""
        headers = {
            "ODS-from": "test-ods",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            MissingOrEmptyHeaderError,
            match='Missing or empty required header "Ssp-TraceID"',
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_trace_id_header_is_whitespace(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """
        Test that ValueError is raised when Ssp-TraceID header contains only whitespace.
        """
        headers = {
            "Ssp-TraceID": "   ",
            "ODS-from": "test-ods",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            MissingOrEmptyHeaderError,
            match='Missing or empty required header "Ssp-TraceID"',
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_missing_content_type_header_is_accepted(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """Test that a missing Content-Type header does not raise an error."""
        headers = {
            "Content-Type": "",
            "Ssp-TraceID": "test-trace-id",
            "ODS-from": "test-ods",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        GetStructuredRecordRequest(request=mock_request)

    def test_raises_unsupported_media_type_when_content_type_is_invalid(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        """
        Test that UnsupportedMediaTypeError is raised when Content-Type
        is not "application/fhir+json".
        """
        headers = {
            "Content-Type": "application/json",
            "Ssp-TraceID": "test-trace-id",
            "ODS-from": "test-ods",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(UnsupportedMediaTypeError):
            GetStructuredRecordRequest(request=mock_request)
