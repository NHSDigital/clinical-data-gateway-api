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
from typing import Any

from requests import Response

from stubs.base_stub import StubBase
from stubs.data.bundles import Bundles


class GpProviderStub(StubBase):
    """
    A minimal in-memory stub for a Provider GP System FHIR API,
    implementing only accessRecordStructured to read basic
    demographic data for a single patient.

    Seeded with an example
    FHIR/STU3 Patient resource with only administrative data based on Example 2
    # https://simplifier.net/guide/gp-connect-access-record-structured/Home/Examples/Allergy-examples?version=1.6.2
    """

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

        try:
            nhs_number = json.loads(body)["parameter"][0]["valueIdentifier"]["value"]
        except (json.JSONDecodeError, KeyError, IndexError):
            return self._create_response(
                status_code=400,
                json_data={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "invalid",
                            "diagnostics": "Malformed request body",
                        }
                    ],
                },
            )

        if nhs_number == "9999999999":
            return self._create_response(
                status_code=200,
                json_data=Bundles.ALICE_JONES_9999999999,
            )

        return self._create_response(
            status_code=404,
            json_data={
                "resourceType": "OperationOutcome",
                "issue": [
                    {
                        "severity": "error",
                        "code": "not-found",
                        "diagnostics": "Patient not found",
                    }
                ],
            },
        )

    def post(
        self,
        _url: str,
        data: str,
        _json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Handle HTTP POST requests for the stub.

        :param url: Request URL.
        :param headers: Request headers.
        :param data: Request body data.
        :param timeout: Request timeout in seconds.
        :return: A :class:`requests.Response` instance.
        """
        trace_id = kwargs.get("headers", {}).get("Ssp-TraceID", "no-trace-id")
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
