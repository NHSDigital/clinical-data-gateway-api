"""Consumer contract tests using Pact for the gateway API.

This test suite acts as a consumer that defines the expected
interactions with the provider (the Flask API).
"""

import json

import requests
from pact import Pact


class TestConsumerContract:
    """Consumer contract tests to define expected API behavior."""

    def test_get_structured_record(self) -> None:
        """Test the consumer's expectation of the get structured record endpoint."""
        pact = Pact(consumer="GatewayAPIConsumer", provider="GatewayAPIProvider")

        expected_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "meta": {
                "profile": [
                    "https://fhir.nhs.uk/STU3/StructureDefinition/GPConnect-StructuredRecord-Bundle-1"
                ]
            },
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        # The API returns this specific UUID, not the NHS number as ID
                        "id": "9999999999",
                        "meta": {
                            "versionId": "1",
                            "lastUpdated": "2020-01-01T00:00:00Z",
                        },
                        "identifier": [
                            {
                                "system": "https://fhir.nhs.uk/Id/nhs-number",
                                "value": "9999999999",
                            }
                        ],
                        "name": [
                            {
                                "use": "official",
                                "family": "Jones",
                                "given": ["Alice"],
                                "period": {"start": "1900-01-01", "end": "9999-12-31"},
                            }
                        ],
                        "gender": "female",
                        "birthDate": "1980-01-01",
                        "generalPractitioner": [
                            {
                                "id": "1",
                                "type": "Organization",
                                "identifier": {
                                    "value": "A12345",
                                    "period": {
                                        "start": "2020-01-01",
                                        "end": "9999-12-31",
                                    },
                                },
                            }
                        ],
                    }
                }
            ],
        }

        # Define the expected interaction
        (
            pact.upon_receiving("a request for structured record")
            .with_request(
                method="POST",
                path="/patient/$gpc.getstructuredrecord",
            )
            .with_header("Content-Type", "application/fhir+json")
            .with_header("ODS-from", "A12345")
            .with_header("Ssp-TraceID", "trace-1234")
            .with_body(
                {
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
                },
                content_type="application/fhir+json",
            )
            .will_respond_with(status=200)
            .with_header("Content-Type", "application/fhir+json")
            .with_body(expected_bundle, content_type="application/fhir+json")
        )

        # Start the mock server and execute the test
        with pact.serve() as server:
            response = requests.post(
                f"{server.url}/patient/$gpc.getstructuredrecord",
                data=json.dumps(
                    {
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
                ),
                headers={
                    "Content-Type": "application/fhir+json",
                    "ODS-from": "A12345",
                    "Ssp-TraceID": "trace-1234",
                },
                timeout=10,
            )

            assert response.status_code == 200
            # Basic assertion to ensure the test itself passes
            assert (
                response.json()["entry"][0]["resource"]["name"][0]["family"] == "Jones"
            )

        # Write the pact file
        pact.write_file("tests/contract/pacts")

    def test_get_nonexistent_route(self) -> None:
        """Test the consumer's expectation when requesting a non-existent route."""
        pact = Pact(consumer="GatewayAPIConsumer", provider="GatewayAPIProvider")

        (
            pact.upon_receiving("a request for a non-existent route")
            .with_request(method="GET", path="/nonexistent")
            .will_respond_with(status=404)
        )

        with pact.serve() as server:
            response = requests.get(f"{server.url}/nonexistent", timeout=10)
            assert response.status_code == 404

        pact.write_file("tests/contract/pacts")
