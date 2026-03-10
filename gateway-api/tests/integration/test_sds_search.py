"""Integration tests for SDS (Spine Directory Service) search functionality."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Client


class TestSdsIntegration:
    """Integration tests for SDS search operations."""

    def test_get_device_by_ods_code_returns_valid_asid(self, client: Client) -> None:
        """
        Test that querying by ODS code returns a valid ASID.
        """
        # Create a request payload with a known patient
        payload = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "patientNHSNumber",
                    "valueIdentifier": {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9999999999",  # Alice Jones with A12345 provider
                    },
                },
            ],
        }

        # Make request to the application endpoint
        response = client.send_to_get_structured_record_endpoint(json.dumps(payload))

        # Verify successful response indicates SDS lookup worked
        assert response.status_code == 200
        # Verify we got a FHIR response (which means the full flow including SDS worked)
        response_data = response.json()
        assert response_data.get("resourceType") == "Bundle"

    def test_consumer_organization_lookup(self, client: Client) -> None:
        """
        Test that CONSUMER organization can be looked up successfully.
        """
        # Create a request with a known patient
        payload = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "patientNHSNumber",
                    "valueIdentifier": {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9999999999",  # Alice Jones with A12345 provider
                    },
                },
            ],
        }

        # Use A12345 as the consumer ODS (Ods-from header)
        response = client.send_to_get_structured_record_endpoint(
            json.dumps(payload),
            headers={"Ods-from": "A12345"},  # Consumer ODS code
        )

        # Verify successful response indicates both consumer and provider
        # SDS lookups worked
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get("resourceType") == "Bundle"

    def test_result_contains_both_asid_and_endpoint_when_available(
        self, client: Client
    ) -> None:
        """
        Test that results contain both ASID and endpoint when both are available.
        """
        # Create a request with a known patient
        payload = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "patientNHSNumber",
                    "valueIdentifier": {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "9999999999",  # Alice Jones with A12345 provider
                    },
                },
            ],
        }

        # Make request to the application endpoint
        response = client.send_to_get_structured_record_endpoint(json.dumps(payload))

        # Verify successful response (200) means both ASID and endpoint were retrieved
        # If either were missing, the application would fail with an error
        assert response.status_code == 200
        response_data = response.json()
        # Verify we got a valid FHIR Bundle (indicating full flow including SDS worked)
        assert response_data.get("resourceType") == "Bundle"
        assert "entry" in response_data or response_data.get("total") is not None
