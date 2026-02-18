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

from gateway_api.common.common import json_str
from requests import Response
from requests.structures import CaseInsensitiveDict

from stubs.data.bundles import Bundles


def _create_response(
    status_code: int,
    headers: dict[str, str] | CaseInsensitiveDict[str],
    content: bytes,
    reason: str = "",
) -> Response:
    """
    Create a :class:`requests.Response` object for the stub.

    :param status_code: HTTP status code.
    :param headers: Response headers dictionary.
    :param content: Response body as bytes.
    :param reason: HTTP reason phrase (e.g., "OK", "Bad Request").
    :return: A :class:`requests.Response` instance.
    """
    response = Response()
    response.status_code = status_code
    response.headers = CaseInsensitiveDict(headers)
    response._content = content  # noqa: SLF001
    response.reason = reason
    response.encoding = "utf-8"
    return response


class GpProviderStub:
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
            return _create_response(
                status_code=400,
                headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
                content=(
                    b'{"resourceType":"OperationOutcome","issue":['
                    b'{"severity":"error","code":"invalid",'
                    b'"diagnostics":"Invalid for testing"}]}'
                ),
                reason="Bad Request",
            )

        try:
            nhs_number = json.loads(body)["parameter"][0]["valueIdentifier"]["value"]
        except (json.JSONDecodeError, KeyError, IndexError):
            return _create_response(
                status_code=400,
                headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
                content=(
                    b'{"resourceType":"OperationOutcome","issue":['
                    b'{"severity":"error","code":"invalid",'
                    b'"diagnostics":"Malformed request body"}]}'
                ),
                reason="Bad Request",
            )

        if nhs_number == "9999999999":
            return _create_response(
                status_code=200,
                headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
                content=json.dumps(Bundles.ALICE_JONES_9999999999).encode("utf-8"),
                reason="OK",
            )

        return _create_response(
            status_code=404,
            headers=CaseInsensitiveDict({"Content-Type": "application/fhir+json"}),
            content=(
                b'{"resourceType":"OperationOutcome","issue":['
                b'{"severity":"error","code":"not-found",'
                b'"diagnostics":"Patient not found"}]}'
            ),
            reason="Not Found",
        )

    def post(
        self,
        url: str,  # NOQA ARG001 # NOSONAR S1172 (unused in stub)
        headers: dict[str, Any],
        data: json_str,
        timeout: int,  # NOQA ARG001 # NOSONAR S1172 (unused in stub)
    ) -> Response:
        """A stubbed requests.post function that routes to the GPProviderStub."""
        _provider_stub = GpProviderStub()
        trace_id = headers.get("Ssp-TraceID", "no-trace-id")
        return _provider_stub.access_record_structured(trace_id, data)
