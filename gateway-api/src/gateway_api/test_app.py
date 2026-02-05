"""Unit tests for the Flask app endpoints."""

import json
import os
from collections.abc import Generator
from copy import copy

import pytest
from fhir.bundle import Bundle
from fhir.parameters import Parameters
from flask import Flask
from flask.testing import FlaskClient
from pytest_mock import MockerFixture

from gateway_api.app import app, get_app_host, get_app_port
from gateway_api.common.common import FlaskResponse


@pytest.fixture
def client() -> Generator[FlaskClient[Flask], None, None]:
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestAppInitialization:
    def test_get_app_host_returns_set_host_name(self) -> None:
        os.environ["FLASK_HOST"] = "host_is_set"

        actual = get_app_host()
        assert actual == "host_is_set"

    def test_get_app_host_raises_runtime_error_if_host_name_not_set(self) -> None:
        del os.environ["FLASK_HOST"]

        with pytest.raises(RuntimeError):
            _ = get_app_host()

    def test_get_app_port_returns_set_port_number(self) -> None:
        os.environ["FLASK_PORT"] = "8080"

        actual = get_app_port()
        assert actual == 8080

    def test_get_app_port_raises_runtime_error_if_port_not_set(self) -> None:
        del os.environ["FLASK_PORT"]

        with pytest.raises(RuntimeError):
            _ = get_app_port()


class TestGetStructuredRecord:
    @pytest.mark.usefixtures("mock_positive_return_value_from_controller_run")
    def test_valid_get_structured_record_request_returns_bundle(
        self,
        get_structured_record_response: Flask,
    ) -> None:
        expected_body_wihtout_timestamp = {
            "resourceType": "Bundle",
            "id": "example-patient-bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "https://example.com/Patient/9999999999",
                    "resource": {
                        "name": [
                            {"family": "Alice", "given": ["Johnson"], "use": "Ally"}
                        ],
                        "gender": "female",
                        "birthDate": "1990-05-15",
                        "resourceType": "Patient",
                        "id": "9999999999",
                        "identifier": [
                            {"value": "9999999999", "system": "urn:nhs:numbers"}
                        ],
                    },
                }
            ],
        }

        actual_body_without_timestamp = get_structured_record_response.get_json()
        del actual_body_without_timestamp["timestamp"]

        assert actual_body_without_timestamp == expected_body_wihtout_timestamp

    @pytest.mark.usefixtures("mock_positive_return_value_from_controller_run")
    def test_valid_get_structured_record_request_returns_200(
        self,
        get_structured_record_response: Flask,
    ) -> None:
        assert get_structured_record_response.status_code == 200

    @pytest.mark.usefixtures("mock_raise_error_from_controller_run")
    def test_get_structured_record_returns_500_when_an_uncaught_exception_is_raised(
        self,
        get_structured_record_response: Flask,
    ) -> None:
        actual_status_code = get_structured_record_response.status_code
        assert actual_status_code == 500

    @pytest.mark.parametrize(
        ("missing_header_key", "expected_message"),
        [
            pytest.param(
                "ODS-from",
                b'Missing or empty required header "ODS-from"',
                id="missing ODS code",
            ),
            pytest.param(
                "Ssp-TraceID",
                b'Missing or empty required header "Ssp-TraceID"',
                id="missing trace id",
            ),
        ],
    )
    def test_get_structured_record_request_returns_400_when_required_header_missing(
        self,
        client: FlaskClient[Flask],
        valid_simple_request_payload: "Parameters",
        valid_headers: dict[str, str],
        missing_header_key: str,
        expected_message: bytes,
    ) -> None:
        invalid_headers = copy(valid_headers)
        del invalid_headers[missing_header_key]

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers=invalid_headers,
        )

        assert response.status_code == 400
        assert "text/plain" in response.content_type
        assert expected_message in response.data

    def test_get_structured_record_returns_500_when_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
    ) -> None:
        assert get_structured_record_response_using_invalid_json_body.status_code == 500

    def test_get_structured_record_returns_content_type_textplain_for_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
    ) -> None:
        assert (
            "text/plain"
            in get_structured_record_response_using_invalid_json_body.content_type
        )

    def test_get_structured_record_returns_intenral_server_error_when_invalid_json_sent(
        self, get_structured_record_response_using_invalid_json_body: Flask
    ) -> None:
        assert (
            b"Internal Server Error:"
            in get_structured_record_response_using_invalid_json_body.data
        )

    @staticmethod
    @pytest.fixture
    def get_structured_record_response(
        client: FlaskClient[Flask],
        valid_headers: dict[str, str],
        valid_simple_request_payload: Parameters,
    ) -> Flask:
        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers=valid_headers,
        )
        return response

    @staticmethod
    @pytest.fixture
    def get_structured_record_response_using_invalid_json_body(
        client: FlaskClient[Flask],
        valid_headers: dict[str, str],
    ) -> Flask:
        invalid_json = "invalid json data"

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            data=invalid_json,
            headers=valid_headers,
        )
        return response

    @staticmethod
    @pytest.fixture
    def mock_positive_return_value_from_controller_run(
        mocker: MockerFixture,
        valid_headers: dict[str, str],
        valid_simple_response_payload: Bundle,
    ) -> None:
        postive_response = FlaskResponse(
            status_code=200,
            data=json.dumps(valid_simple_response_payload),
            headers=valid_headers,
        )
        mocker.patch(
            "gateway_api.controller.Controller.run", return_value=postive_response
        )

    @staticmethod
    @pytest.fixture
    def mock_raise_error_from_controller_run(
        mocker: MockerFixture,
    ) -> None:
        internal_error = ValueError("Test exception")
        mocker.patch(
            "gateway_api.controller.Controller.run", side_effect=internal_error
        )


class TestHealthCheck:
    def test_health_check_returns_200_and_healthy_status(
        self, client: FlaskClient[Flask]
    ) -> None:
        response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"

    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
    def test_health_check_only_accepts_get_method(
        self, client: FlaskClient[Flask], method: str
    ) -> None:
        """Test that health_check only accepts GET method."""
        response = client.open("/health", method=method)
        assert response.status_code == 405
