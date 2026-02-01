"""Integration tests for the gateway API using pytest."""

import json

from fhir.parameters import Parameters
from stubs.stub_provider import GpProviderStub

from tests.conftest import Client


class TestGetStructuredRecord:
    def test_happy_path_returns_200(
        self, client: Client, simple_request_payload: Parameters
    ) -> None:
        """Test that the root endpoint returns a 200 status code."""
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert response.status_code == 200

    def test_happy_path_returns_correct_message(
        self,
        client: Client,
        simple_request_payload: Parameters,
    ) -> None:
        """Test that the root endpoint returns the correct message."""
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert response.json() == GpProviderStub.patient_bundle

    def test_happy_path_content_type(
        self, client: Client, simple_request_payload: Parameters
    ) -> None:
        """Test that the response has the correct content type."""
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(simple_request_payload)
        )
        assert "application/fhir+json" in response.headers["Content-Type"]
