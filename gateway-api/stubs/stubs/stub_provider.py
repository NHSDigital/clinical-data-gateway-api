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

from typing import Any

from requests import Response

from stubs.base_stub import StubBase


class GpProviderStub(StubBase):
    """
    A minimal in-memory stub for a Provider GP System FHIR API,
    implementing only accessRecordStructured to read basic
    demographic data for a single patient.

    Seeded with an example
    FHIR/STU3 Patient resource with only administrative data based on Example 2
    # https://simplifier.net/guide/gp-connect-access-record-structured/Home/Examples/Allergy-examples?version=1.6.2
    """

    # Example patient resource
    patient_bundle = {
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
        body: str,  # NOQA ARG002 # NOSONAR S1172: unused parameter maintains method signature in stub
    ) -> Response:
        """
        Simulate accessRecordStructured operation of GPConnect FHIR API.

        returns:
            Response: The stub patient bundle wrapped in a Response object.
        """
        if trace_id == "invalid for test":
            return self._create_response(
                status_code=400,
                headers={"Content-Type": "application/fhir+json"},
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": "Invalid for testing",
                        }
                    ],
                },
            )

        return self._create_response(
            status_code=200,
            headers={"Content-Type": "application/fhir+json"},
            json_data=self.patient_bundle,
        )

    def post(
        self,
        url: str,  # NOQA ARG001 # NOSONAR S1172 (unused in stub)
        headers: dict[str, Any],
        data: str,
        timeout: int,  # NOQA ARG001 # NOSONAR S1172 (unused in stub)
    ) -> Response:
        """
        Handle HTTP POST requests for the stub.

        :param url: Request URL.
        :param headers: Request headers.
        :param data: Request body data.
        :param timeout: Request timeout in seconds.
        :return: A :class:`requests.Response` instance.
        """
        trace_id = headers.get("Ssp-TraceID", "no-trace-id")
        return self.access_record_structured(trace_id, data)

    def get(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        timeout: int,
    ) -> Response:
        """
        Handle HTTP GET requests for the stub.

        :param url: Request URL.
        :param headers: Request headers.
        :param params: Query parameters.
        :param timeout: Request timeout in seconds.
        :raises NotImplementedError: GET requests are not supported by this stub.
        """
        raise NotImplementedError("GET requests are not supported by GpProviderStub")
