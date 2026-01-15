"""
Minimal in-memory stub for a Provider GP System FHIR API,
implementing only accessRecordStructured to read basic
demographic data for a single patient.

    Contract elements for direct provider call inferred from from
    GPConnect documentation:
    https://developer.nhs.uk/apis/gpconnect/accessrecord_structured_development_retrieve_patient_record.html
        - Method: POST
        - fhir_base: /FHIR/STU3
        - resource: /Patient
        - fhir_operation: $gpc.getstructruredrecord

        Headers:
            Ssp-TraceID: Consumer's Trace ID (a GUID or UUID)
            Ssp-From: Consumer's ASID
            Ssp-To:	Provider's ASID
            Ssp-InteractionID:
                urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1

        Request Body JSON (FHIR STU3 Parameters resource with patient NHS number.
        Later add optional parameters such as `includeAllergies`):
            {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "patientNHSNumber",
                        "valueIdentifier": {
                            "system": "https://fhir.nhs.uk/Id/nhs-number",
                            "value": "9999999999"
                        }
                    }
                ]
            }


        return

"""

from requests import Response


class GPProviderStub:
    """
    A minimal in-memory stub for a Provider GP System FHIR API,
    implementing only accessRecordStructured to read basic
    demographic data for a single patient.
    """

    def __init__(self) -> None:
        """Create a GPProviderStub instance."""
        # Seed an example matching the spec's id example stubResponse
        # FHIR/STU3 Patient resource with only administrative data based on Example 2
        # https://simplifier.net/guide/gp-connect-access-record-structured/Home/Examples/Allergy-examples?version=1.6.2
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

    def access_record_structured(self) -> Response:
        """
        Simulate accessRecordStructured operation of GPConnect FHIR API.

        returns:
            Response: The stub patient bundle wrapped in a Response object.
        """

        response = Response()
        response.status_code = 200

        return response
