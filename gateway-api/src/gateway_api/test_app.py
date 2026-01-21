"""Unit tests for the Flask app endpoints."""

from collections.abc import Generator
from typing import TYPE_CHECKING

import pytest
from flask import Flask
from flask.testing import FlaskClient

from gateway_api.app import app

if TYPE_CHECKING:
    from fhir.parameters import Parameters


@pytest.fixture
def client() -> Generator[FlaskClient[Flask], None, None]:
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGetStructuredRecord:
    def test_get_structured_record_returns_200_with_bundle(
        self, client: FlaskClient[Flask]
    ) -> None:
        body: Parameters = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "patientNHSNumber",
                    "valueIdentifier": {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9999999999",
                    },
                },
            ],
        }
        response = client.post("/patient/$gpc.getstructuredrecord", json=body)

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
