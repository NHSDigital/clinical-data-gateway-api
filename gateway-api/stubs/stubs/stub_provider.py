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


        return stubResponse with FHIR STU3 Patient resource JSON with only
        administrative data:
            {
                "resourceType": "Patient",
                "id": "example",
                "identifier": [
                    {
                        "system": "https://fhir.nhs.uk/Id/nhs-number",
                        "value": "1234567890"
                    }
                ],
                "name": [
                    {
                        "use": "official",
                        "family": "Doe",
                        "given": [
                            "John"
                        ]
                    }
                ],
                "gender": "male",
                "birthDate": "1980-01-01"
            }

"""
