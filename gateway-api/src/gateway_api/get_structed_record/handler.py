from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fhir import Bundle

from gateway_api.get_structed_record.request import GetStructuredRecordRequest


class GetStructuredRecordHandler:
    @classmethod
    def handle(cls, request: GetStructuredRecordRequest) -> None:
        bundle: Bundle = {
            "resourceType": "Bundle",
            "id": "example-patient-bundle",
            "type": "collection",
            "timestamp": "2026-01-12T10:00:00Z",
            "entry": [
                {
                    "fullUrl": "urn:uuid:123e4567-e89b-12d3-a456-426614174000",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "9999999999",
                        "identifier": [
                            {
                                "system": "https://fhir.nhs.uk/Id/nhs-number",
                                "value": "9999999999",
                            }
                        ],
                        "name": [
                            {"use": "official", "family": "Doe", "given": ["John"]}
                        ],
                        "gender": "male",
                        "birthDate": "1985-04-12",
                    },
                }
            ],
        }
        request.set_positive_response(bundle)
