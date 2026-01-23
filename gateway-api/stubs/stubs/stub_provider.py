"""
Minimal in-memory stub for a Provider GP System FHIR API,
implementing only accessRecordStructured to read basic
demographic data for a single patient.

Contract elements for direct provider calls are inferred from
GPConnect documentation:
https://developer.nhs.uk/apis/gpconnect/accessrecord_structured_development_retrieve_patient_record.html
    - Method: POST
    - fhir_base: /FHIR/STU3
    - resource: /Patient
    - fhir_operation: $gpc.getstructuredrecord

Headers:
    Ssp-TraceID: Consumer's Trace ID (a GUID or UUID)
    Ssp-From: Consumer's ASID
    Ssp-To: Provider's ASID
    Ssp-InteractionID:
        urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1

Request Body JSON (FHIR STU3 Parameters resource with patient NHS number.
"""

import json

from requests import Response
from requests.structures import CaseInsensitiveDict


class StubResponse(Response):
    """A stub response object representing a minimal FHIR + JSON response."""

    def __init__(
        self,
        status_code: int,
        _content: bytes,
        headers: CaseInsensitiveDict[str],
        reason: str,
    ) -> None:
        """Create a FakeResponse instance."""
        super().__init__()
        self.status_code = status_code
        self._content = _content
        self.headers = CaseInsensitiveDict(headers)
        self.reason = reason
        self.encoding = "utf-8"


class GpProviderStub:
    """
    A minimal in-memory stub for a Provider GP System FHIR API,
    implementing only accessRecordStructured to read basic
    demographic data for a single patient.
    """

    def __init__(self) -> None:
        """Create a GPProviderStub instance which is seeded with an example
        FHIR/STU3 Patient resource with only administrative data based on Example 2
        # https://simplifier.net/guide/gp-connect-access-record-structured/Home/Examples/Allergy-examples?version=1.6.2
        """
        self.patient_bundle = {
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
                        "id": "04603d77-1a4e-4d63-b246-d7504f8bd833",
                        "meta": {
                            "versionId": "1469448000000",
                            "profile": [
                                "https://fhir.nhs.uk/STU3/StructureDefinition/CareConnect-GPC-Patient-1"
                            ],
                        },
                        "identifier": [
                            {
                                "system": "https://fhir.nhs.uk/Id/nhs-number",
                                "value": "9999999999",
                            }
                        ],
                        "active": True,
                        "name": [
                            {
                                "use": "official",
                                "text": "JACKSON Jane (Miss)",
                                "family": "Jackson",
                                "given": ["Jane"],
                                "prefix": ["Miss"],
                            }
                        ],
                        "gender": "female",
                        "birthDate": "1952-05-31",
                    }
                }
            ],
        }

    def access_record_structured(
        self,
        trace_id: str,
        body: str,  # NOSONAR S1172: unused parameter maintains method signature in stub
    ) -> StubResponse:
        """
        Simulate accessRecordStructured operation of GPConnect FHIR API.

        returns:
            Response: The stub patient bundle wrapped in a Response object.
        """

        stub_response = StubResponse(
            status_code=200,
            headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
            reason="OK",
            _content=json.dumps(self.patient_bundle).encode("utf-8"),
        )

        if trace_id == "invalid for test":
            return StubResponse(
                status_code=400,
                headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
                reason="Bad Request",
                _content=(
                    b'{"resourceType":"OperationOutcome","issue":['
                    b'{"severity":"error","code":"invalid",'
                    b'"diagnostics":"Invalid for testing"}]}'
                ),
            )

        return stub_response
