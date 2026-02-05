"""Unit tests for the Flask app endpoints."""

import json
import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from flask import Flask
from flask.testing import FlaskClient

from gateway_api.app import app, get_app_host, get_app_port
from gateway_api.controller import Controller
from gateway_api.get_structured_record.request import GetStructuredRecordRequest

if TYPE_CHECKING:
    from fhir.parameters import Parameters


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
        monkeypatch: pytest.MonkeyPatch,
        valid_simple_request_payload: "Parameters",
    ) -> None:
        """Test that successful controller response is returned correctly."""
        from datetime import datetime, timezone
        from typing import Any

        from gateway_api.common.common import FlaskResponse

        # Mock the controller to return a successful FlaskResponse with a Bundle
        mock_bundle_data: Any = {
            "resourceType": "Bundle",
            "id": "example-patient-bundle",
            "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": [
                {
                    "fullUrl": "http://example.com/Patient/9999999999",
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

        def mock_run(
            self: Controller,  # noqa: ARG001
            request: GetStructuredRecordRequest,  # noqa: ARG001
        ) -> FlaskResponse:
            return FlaskResponse(
                status_code=200,
                data=json.dumps(mock_bundle_data),
                headers={"Content-Type": "application/fhir+json"},
            )

        monkeypatch.setattr(
            "gateway_api.controller.Controller.run",
            mock_run,
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

    def test_get_structured_record_handles_exception(
        self,
        client: FlaskClient[Flask],
        monkeypatch: pytest.MonkeyPatch,
        valid_simple_request_payload: "Parameters",
    ) -> None:
        """
        Test that exceptions during controller execution are caught and return 500.
        """

        # This is mocking the run method of the Controller
        # and therefore self is a Controller
        def mock_run_with_exception(
            self: Controller,  # noqa: ARG001
            request: GetStructuredRecordRequest,  # noqa: ARG001
        ) -> None:
            raise ValueError("Test exception")

        monkeypatch.setattr(
            "gateway_api.controller.Controller.run",
            mock_run_with_exception,
        )

        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers={
                "Ssp-TraceID": "test-trace-id",
                "ODS-from": "test-ods",
            },
        )
        assert response.status_code == 500

    def test_get_structured_record_handles_request_validation_error(
        self,
        client: FlaskClient[Flask],
        valid_simple_request_payload: "Parameters",
    ) -> None:
        """Test that RequestValidationError returns 400 with error message."""
        # Create a request missing the required ODS-from header
        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            json=valid_simple_request_payload,
            headers={
                "Ssp-TraceID": "test-trace-id",
                # Missing "ODS-from" header to trigger RequestValidationError
            },
        )

        assert response.status_code == 400
        assert "text/plain" in response.content_type
        assert b'Missing or empty required header "ODS-from"' in response.data

    def test_get_structured_record_handles_unexpected_exception_during_init(
        self,
        client: FlaskClient[Flask],
    ) -> None:
        """Test that unexpected exceptions during request init return 500."""
        # Send invalid JSON to trigger an exception during request processing
        response = client.post(
            "/patient/$gpc.getstructuredrecord",
            data="invalid json data",
            headers={
                "Ssp-TraceID": "test-trace-id",
                "ODS-from": "test-ods",
                "Content-Type": "application/fhir+json",
            },
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
