"""Unit tests for the Flask app endpoints."""

import os
from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from flask import Flask
from flask.testing import FlaskClient

from gateway_api.app import app, get_app_host, get_app_port

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
        self, client: FlaskClient[Flask], valid_simple_request_payload: "Parameters"
    ) -> None:
        response = client.post(
            "/patient/$gpc.getstructuredrecord", json=valid_simple_request_payload
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
        monkeypatch.setattr(
            "gateway_api.get_structured_record.GetStructuredRecordHandler.handle",
            Exception(),
        )

        response = client.post(
            "/patient/$gpc.getstructuredrecord", json=valid_simple_request_payload
        )
        assert response.status_code == 500


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
