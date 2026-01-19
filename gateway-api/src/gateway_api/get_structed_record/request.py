from fhir import Bundle
from flask.wrappers import Request


class GetStructuredRecordRequest:
    def __init__(self, request: Request) -> None:
        self._http_request = request

    def fulfil(self) -> Bundle:
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
        return bundle
