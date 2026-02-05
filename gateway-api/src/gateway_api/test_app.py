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
    def test_get_structured_record_returns_200_with_bundle(
        self,
        client: FlaskClient[Flask],
        mocker: MockerFixture,
        valid_simple_request_payload: Parameters,
        valid_simple_response_payload: Bundle,
    ) -> None:
        """Test that successful controller response is returned correctly."""

        postive_response = FlaskResponse(
            status_code=200,
            data=json.dumps(valid_simple_response_payload),
            headers={"Content-Type": "application/fhir+json"},
        )
        mocker.patch(
            "gateway_api.controller.Controller.run", return_value=postive_response
        )

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers={
                "Ssp-TraceID": "test-trace-id",
                "ODS-from": "test-ods",
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert data.get("resourceType") == "Bundle"
        assert data.get("id") == "example-patient-bundle"
        assert data.get("type") == "collection"
        assert "entry" in data
        assert isinstance(data["entry"], list)
        assert len(data["entry"]) > 0
        assert data["entry"][0]["resource"]["resourceType"] == "Patient"
        assert data["entry"][0]["resource"]["id"] == "9999999999"
        assert data["entry"][0]["resource"]["identifier"][0]["value"] == "9999999999"

    def test_get_structured_record_returns_500_when_an_uncaught_exception_is_raised(
        self,
        client: FlaskClient[Flask],
        mocker: MockerFixture,
        valid_simple_request_payload: "Parameters",
        valid_headers: dict[str, str],
    ) -> None:
        internal_error = ValueError("Test exception")
        mocker.patch(
            "gateway_api.controller.Controller.run", side_effect=internal_error
        )

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers=valid_headers,
        )
        assert response.status_code == 500

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
        """Test that RequestValidationError returns 400 with error message."""
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

    def test_get_structured_record_handles_invalid_json_data(
        self, client: FlaskClient[Flask], valid_headers: dict[str, str]
    ) -> None:
        """Test that unexpected exceptions during request init return 500."""
        invalid_json = "invalid json data"

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            data=invalid_json,
            headers=valid_headers,
        )

        assert response.status_code == 500
        assert "text/plain" in response.content_type
        assert b"Internal Server Error:" in response.data


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
