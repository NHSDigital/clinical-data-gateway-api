import json
from typing import Any
from unittest.mock import Mock

from flask import request
from requests.structures import CaseInsensitiveDict

from gateway_api.app import app
from gateway_api.common.error import UnexpectedError
from gateway_api.get_structured_record import GetStructuredRecordResponse


class TestGetStructuredRecordResponse:
    def test_mirror_headers_adds_request_headers_to_response(
        self, valid_simple_request_payload: dict[str, Any]
    ) -> None:
        headers_to_be_mirrored = CaseInsensitiveDict({"Ssp-TraceId": "a_trace_id"})

        with app.test_request_context(
            "/patient/$gpc.getstructuredrecord",
            method="POST",
            data=json.dumps(valid_simple_request_payload),
            headers=headers_to_be_mirrored,
        ):
            response = GetStructuredRecordResponse()
            response.mirror_headers(request)

            assert response.headers is not None, (
                "Expected headers to be set, but they were None"
            )
            assert all(
                response.headers.get(key) == value
                for key, value in headers_to_be_mirrored.items()
            ), "Expected response headers to match request headers, but they did not"

    def test_add_provider_response_adds_provider_response_body(
        self, valid_simple_response_payload: dict[str, Any]
    ) -> None:
        provider_response = Mock()
        provider_response.status_code = 200
        provider_response.json.return_value = valid_simple_response_payload

        response = GetStructuredRecordResponse()
        response.add_provider_response(provider_response)

        actual = response.build().json
        assert actual == valid_simple_response_payload, (
            "Actual response body did not match expected response body."
        )

    def test_add_provider_response_adds_200_status(
        self, valid_simple_response_payload: dict[str, Any]
    ) -> None:
        provider_response = Mock()
        provider_response.status_code = 200
        provider_response.json.return_value = valid_simple_response_payload

        response = GetStructuredRecordResponse()
        response.add_provider_response(provider_response)

        actual = response.build().status_code
        assert actual == 200, f"Expected status code to be 200, but got {actual}"

    def test_add_error_response_adds_error_response_body(self) -> None:
        error = UnexpectedError(traceback="something broke")

        response = GetStructuredRecordResponse()
        response.add_error_response(error)

        expected_response_body = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": "Internal Server Error: something broke",
                }
            ],
        }
        actual_response_body = response.build().json
        assert actual_response_body == expected_response_body, (
            "Actual response body did not match expected response body."
        )
