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

    def test_raises_value_error_when_ods_from_header_is_missing(
        self, valid_simple_request_payload: Parameters
    ) -> None:
        """Test that ValueError is raised when ODS-from header is missing."""
        headers = {
            "Ssp-TraceID": "test-trace-id",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            RequestValidationError, match='Missing or empty required header "ODS-from"'
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_ods_from_header_is_whitespace(
        self, valid_simple_request_payload: Parameters
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
            RequestValidationError, match='Missing or empty required header "ODS-from"'
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_trace_id_header_is_missing(
        self, valid_simple_request_payload: Parameters
    ) -> None:
        """Test that ValueError is raised when Ssp-TraceID header is missing."""
        headers = {
            "ODS-from": "test-ods",
        }
        mock_request = create_mock_request(headers, valid_simple_request_payload)

        with pytest.raises(
            RequestValidationError,
            match='Missing or empty required header "Ssp-TraceID"',
        ):
            GetStructuredRecordRequest(request=mock_request)

    def test_raises_value_error_when_trace_id_header_is_whitespace(
        self, valid_simple_request_payload: Parameters
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
            RequestValidationError,
            match='Missing or empty required header "Ssp-TraceID"',
        ):
            GetStructuredRecordRequest(request=mock_request)


class TestSetResponseFromFlaskResponse:
    def test_sets_response_body_from_valid_json_data(
        self, mock_request_with_headers: Request
    ) -> None:
        """Test that valid JSON data is correctly parsed and set."""

        request_obj = GetStructuredRecordRequest(request=mock_request_with_headers)

        bundle_data: Bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "type": "collection",
            "timestamp": "2026-02-03T10:00:00Z",
            "entry": [],
        }
        flask_response = FlaskResponse(
            status_code=200,
            data=json.dumps(bundle_data),
            headers={"Content-Type": "application/fhir+json"},
        )

        request_obj.set_response_from_flaskresponse(flask_response)

        resp = request_obj.build_response()
        assert resp.status == "200 OK"
        assert resp.response is not None
        assert cast("list[bytes]", resp.response)[0].decode("utf-8") == json.dumps(
            bundle_data
        )

    def test_handles_json_decode_error(
        self, mock_request_with_headers: Request
    ) -> None:
        """Test that JSONDecodeError is handled and sets negative response."""
        request_obj = GetStructuredRecordRequest(request=mock_request_with_headers)

        flask_response = FlaskResponse(
            status_code=200,
            data="invalid json {not valid}",
            headers={"Content-Type": "application/fhir+json"},
        )

        request_obj.set_response_from_flaskresponse(flask_response)

        resp = request_obj.build_response()
        assert resp.status == "500 INTERNAL SERVER ERROR"
        assert resp.response is not None
        response_data = json.loads(
            cast("list[bytes]", resp.response)[0].decode("utf-8")
        )
        assert response_data["resourceType"] == "OperationOutcome"
        assert len(response_data["issue"]) == 1
        assert (
            "Failed to decode response body:"
            in response_data["issue"][0]["diagnostics"]
        )

    def test_handles_unexpected_exception_during_json_decode(
        self, mock_request_with_headers: Request, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that unexpected exceptions during JSON parsing are handled."""
        request_obj = GetStructuredRecordRequest(request=mock_request_with_headers)

        flask_response = FlaskResponse(
            status_code=200,
            data='{"valid": "json"}',
            headers={"Content-Type": "application/fhir+json"},
        )

        # Mock json.loads to raise an unexpected exception
        original_json_loads = json.loads

        def mock_json_loads(data: str) -> None:  # noqa: ARG001
            raise RuntimeError("Unexpected error during JSON parsing")

        monkeypatch.setattr(json, "loads", mock_json_loads)

        request_obj.set_response_from_flaskresponse(flask_response)

        # Restore json.loads before building response
        monkeypatch.setattr(json, "loads", original_json_loads)

        resp = request_obj.build_response()
        assert resp.status == "500 INTERNAL SERVER ERROR"
        assert resp.response is not None
        response_data = json.loads(
            cast("list[bytes]", resp.response)[0].decode("utf-8")
        )
        assert response_data["resourceType"] == "OperationOutcome"
        assert len(response_data["issue"]) == 1
        assert (
            "Unexpected error decoding response body:"
            in response_data["issue"][0]["diagnostics"]
        )
        assert (
            "Unexpected error during JSON parsing"
            in response_data["issue"][0]["diagnostics"]
        )

    def test_handles_empty_response_data(
        self, mock_request_with_headers: Request
    ) -> None:
        """Test that empty/None response data is handled correctly."""
        request_obj = GetStructuredRecordRequest(request=mock_request_with_headers)

        flask_response = FlaskResponse(
            status_code=404,
            data=None,
            headers={"Content-Type": "application/fhir+json"},
        )

        request_obj.set_response_from_flaskresponse(flask_response)

        resp = request_obj.build_response()
        assert resp.status == "404 NOT FOUND"
        assert resp.response is not None
        response_data = json.loads(
            cast("list[bytes]", resp.response)[0].decode("utf-8")
        )
        assert response_data["resourceType"] == "OperationOutcome"
        assert len(response_data["issue"]) == 1
        assert response_data["issue"][0]["diagnostics"] == "No response body received"

    def test_handles_empty_string_response_data(
        self, mock_request_with_headers: Request
    ) -> None:
        """Test that empty string response data is handled as no data."""
        request_obj = GetStructuredRecordRequest(request=mock_request_with_headers)

        flask_response = FlaskResponse(
            status_code=500,
            data="",
            headers={"Content-Type": "application/fhir+json"},
        )

        request_obj.set_response_from_flaskresponse(flask_response)

        resp = request_obj.build_response()
        assert resp.status == "500 INTERNAL SERVER ERROR"
        assert resp.response is not None
        response_data = json.loads(
            cast("list[bytes]", resp.response)[0].decode("utf-8")
        )
        assert response_data["resourceType"] == "OperationOutcome"
        assert len(response_data["issue"]) == 1
        assert response_data["issue"][0]["diagnostics"] == "No response body received"
