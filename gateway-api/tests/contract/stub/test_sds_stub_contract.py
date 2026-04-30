"""Contract tests for the SDS FHIR API stub.

These tests verify that the :class:`~stubs.sds.stub.SdsFhirApiStub` honours the
``GET /Device`` and ``GET /Endpoint`` contracts described in the SDS OpenAPI
specification:

    https://github.com/NHSDigital/spine-directory-service-api

The stub does not expose an HTTP server, so the tests call its methods directly
and validate the returned :class:`requests.Response` objects against the
contract requirements.
"""

from __future__ import annotations

from typing import Any

import pytest
from fhir.constants import FHIRSystem
from gateway_api.get_structured_record import ACCESS_RECORD_STRUCTURED_INTERACTION_ID
from stubs.sds.stub import SdsFhirApiStub

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

# FHIR-formatted query parameter values used across all tests
_ORG_PROVIDER = f"{FHIRSystem.ODS_CODE}|PROVIDER"
_ORG_UNKNOWN = f"{FHIRSystem.ODS_CODE}|UNKNOWN_ORG_XYZ"

_INTERACTION_ID_PARAM = (
    f"{FHIRSystem.NHS_SERVICE_INTERACTION_ID}|{ACCESS_RECORD_STRUCTURED_INTERACTION_ID}"
)
_VALID_CORRELATION_ID = "test-correlation-id-12345"

_BASE_DEVICE_URL = "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Device"
_BASE_ENDPOINT_URL = (
    "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Endpoint"
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stub() -> SdsFhirApiStub:
    """Return a fresh stub instance pre-seeded with default data."""
    return SdsFhirApiStub()


# ---------------------------------------------------------------------------
# GET /Device – 200 success
# ---------------------------------------------------------------------------


class TestGetDeviceBundleSuccess:
    """Contract tests for the happy-path GET /Device → 200 response."""

    def test_response_matches_expected(self, stub: SdsFhirApiStub) -> None:
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200
        assert "application/fhir+json" in response.headers["Content-Type"]

        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "searchset"

        assert body["total"] == 1
        assert len(body["entry"]) == 1

        entry = body["entry"][0]
        assert entry["resource"]["id"] == "F0F0E921-92CA-4A88-A550-2DBB36F703AF"
        assert (
            entry["fullUrl"]
            == "https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Device/F0F0E921-92CA-4A88-A550-2DBB36F703AF"
        )
        assert entry["search"]["mode"] == "match"

    def test_x_correlation_id_echoed_back_when_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The spec states ``X-Correlation-Id`` is mirrored back in the response."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key", "X-Correlation-Id": _VALID_CORRELATION_ID},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

    def test_x_correlation_id_absent_when_not_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``X-Correlation-Id`` must not appear in the response when not supplied."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert "X-Correlation-Id" not in response.headers

    def test_empty_bundle_returned_for_unknown_org(self, stub: SdsFhirApiStub) -> None:
        """An unknown organisation must return a 200 with an empty Bundle."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={
                "organization": _ORG_UNKNOWN,
                "identifier": _INTERACTION_ID_PARAM,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["total"] == 0
        assert body["entry"] == []


# ---------------------------------------------------------------------------
# GET /Device – Device resource structure
# ---------------------------------------------------------------------------


class TestGetDeviceResourceStructure:
    """Contract tests verifying the shape of returned Device resources."""

    def test_device_resource_type_is_device(self, stub: SdsFhirApiStub) -> None:
        """Each resource inside the Bundle must have ``resourceType: "Device"``."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert len(body["entry"]) == 1

        entry = body["entry"][0]
        resource = entry["resource"]

        assert resource["resourceType"] == "Device"
        assert resource["id"] == "F0F0E921-92CA-4A88-A550-2DBB36F703AF"
        assert resource["owner"]["identifier"]["system"] == FHIRSystem.ODS_CODE

        assert len(resource["identifier"]) == 1
        identifiers = resource["identifier"]
        assert identifiers[0]["system"] == FHIRSystem.NHS_SPINE_ASID
        assert identifiers[0]["value"] == "asid_PROV"


# ---------------------------------------------------------------------------
# GET /Device – 400 validation errors
# ---------------------------------------------------------------------------


class TestGetDeviceBundleValidationErrors:
    """Contract tests for GET /Device → 400 when required inputs are missing."""

    def test_missing_apikey_returns_400(self, stub: SdsFhirApiStub) -> None:
        """The spec requires the ``apikey`` header; its absence must yield 400."""
        response = stub.get_device_bundle(
            headers={},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        self.verify_error_response_body(response, "Missing required header: apikey")

    def test_missing_organization_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``organization`` is a required query parameter for /Device."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        self.verify_error_response_body(
            response, "Missing required query parameter: organization"
        )

    def test_missing_identifier_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``identifier`` is a required query parameter for /Device."""
        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER},
        )
        assert response.status_code == 400
        self.verify_error_response_body(
            response, "Missing required query parameter: identifier"
        )

    def test_missing_apikey_echoes_correlation_id(self, stub: SdsFhirApiStub) -> None:
        """``X-Correlation-Id`` must be echoed even in error responses."""
        response = stub.get_device_bundle(
            headers={"X-Correlation-Id": _VALID_CORRELATION_ID},  # no apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

        self.verify_error_response_body(response, "Missing required header: apikey")

    def verify_error_response_body(
        self, response: Any, expected_diagnostics: str
    ) -> None:
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"

        assert isinstance(body.get("issue"), list)
        assert len(body["issue"]) == 1

        issue = body["issue"][0]
        assert issue["severity"] == "error"

        assert issue["code"] == "invalid"

        assert "diagnostics" in body["issue"][0]
        assert body["issue"][0]["diagnostics"] == expected_diagnostics


# ---------------------------------------------------------------------------
# GET /Endpoint – 200 successful retrieval
# ---------------------------------------------------------------------------


class TestGetEndpointBundleSuccess:
    """Contract tests for the happy-path GET /Endpoint → 200 response."""

    def test_endpoint_bundle_matches_expected_response(
        self, stub: SdsFhirApiStub
    ) -> None:
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200
        assert "application/fhir+json" in response.headers["Content-Type"]

        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "searchset"
        assert body["total"] == len(body["entry"])

        assert len(body["entry"]) == 5
        endpoint_ids = [
            "E0E0E921-92CA-4A88-A550-2DBB36F703AF",
            "E1E1E921-92CA-4A88-A550-2DBB36F703AF",
            "E2E2E921-92CA-4A88-A550-2DBB36F703AF",
            "E3E3E921-92CA-4A88-A550-2DBB36F703AF",
            "E3E3E921-92CA-4A88-A550-2DBB36F703AF",
        ]
        for i in range(len(endpoint_ids)):
            entry = body["entry"][i]

            endpoint_id = endpoint_ids[i]
            assert (
                entry["fullUrl"]
                == f"https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Endpoint/{endpoint_id}"
            )
            assert entry["resource"]["id"] == endpoint_id
            assert entry["search"]["mode"] == "match"

    def test_x_correlation_id_echoed_back_when_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The spec states ``X-Correlation-Id`` is mirrored back in the response."""
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key", "X-Correlation-Id": _VALID_CORRELATION_ID},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

    def test_x_correlation_id_absent_when_not_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``X-Correlation-Id`` must not appear in the response when not supplied."""
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert "X-Correlation-Id" not in response.headers

    def test_empty_bundle_returned_for_unknown_org(self, stub: SdsFhirApiStub) -> None:
        """An organisation not present in the stub must yield an empty Bundle."""
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={
                "organization": _ORG_UNKNOWN,
                "identifier": _INTERACTION_ID_PARAM,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["total"] == 0
        assert body["entry"] == []


# ---------------------------------------------------------------------------
# GET /Endpoint – Endpoint resource structure
# ---------------------------------------------------------------------------


class TestGetEndpointResourceStructure:
    """Contract tests verifying the shape of returned Endpoint resources."""

    def test_endpoint_resource_type_is_endpoint(self, stub: SdsFhirApiStub) -> None:
        """Each resource inside the Bundle must have ``resourceType: "Endpoint"``."""
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={
                "organization": _ORG_PROVIDER,
                "identifier": _INTERACTION_ID_PARAM,
            },
        )
        body = response.json()
        assert len(body["entry"]) == 1

        entry = body["entry"][0]
        resource = entry["resource"]
        assert resource["resourceType"] == "Endpoint"

        assert resource["id"] == "E0E0E921-92CA-4A88-A550-2DBB36F703AF"
        assert resource["status"] == "active"

        ct = resource["connectionType"]
        assert (
            ct["system"]
            == "https://terminology.hl7.org/CodeSystem/endpoint-connection-type"
        )
        assert ct["code"] == "hl7-fhir-rest"

        assert len(resource["payloadType"]) == 1
        assert resource["address"] == "https://provider.example.com/fhir"
        assert (
            resource["managingOrganization"]["identifier"]["system"]
            == FHIRSystem.ODS_CODE
        )

        managing_org = resource["managingOrganization"]
        assert managing_org["identifier"]["system"] == FHIRSystem.ODS_CODE

        assert isinstance(resource["identifier"], list)
        assert len(resource["identifier"]) == 1

        identifiers = resource["identifier"]
        assert identifiers[0]["system"] == FHIRSystem.NHS_SPINE_ASID


# ---------------------------------------------------------------------------
# GET /Endpoint – 400 validation errors
# ---------------------------------------------------------------------------


class TestGetEndpointBundleValidationErrors:
    """Contract tests for GET /Endpoint → 400 when required inputs are missing."""

    def test_missing_apikey_returns_400(self, stub: SdsFhirApiStub) -> None:
        """The spec requires the ``apikey`` header; its absence must yield 400."""
        response = stub.get_endpoint_bundle(
            headers={},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        self.verify_error_response_body(response, "Missing required header: apikey")

    def test_missing_identifier_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``identifier`` is a required query parameter for /Endpoint."""
        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={},
        )
        assert response.status_code == 400
        self.verify_error_response_body(
            response, "Missing required query parameter: identifier"
        )

    def test_missing_apikey_echoes_correlation_id(self, stub: SdsFhirApiStub) -> None:
        """``X-Correlation-Id`` must be echoed even in error responses."""
        response = stub.get_endpoint_bundle(
            headers={"X-Correlation-Id": _VALID_CORRELATION_ID},  # no apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID
        self.verify_error_response_body(response, "Missing required header: apikey")

    def verify_error_response_body(
        self, response: Any, expected_diagnostics: str
    ) -> None:
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"

        assert isinstance(body.get("issue"), list)
        assert len(body["issue"]) == 1

        assert body["issue"][0]["severity"] == "error"
        assert body["issue"][0]["code"] == "invalid"

        assert "diagnostics" in body["issue"][0]
        assert body["issue"][0]["diagnostics"] == expected_diagnostics


# ---------------------------------------------------------------------------
# get() convenience wrapper – routes by URL path
# ---------------------------------------------------------------------------


class TestGetConvenienceMethod:
    """Verify the ``get()`` wrapper routes correctly based on the URL path."""

    def test_device_url_returns_device_bundle(self, stub: SdsFhirApiStub) -> None:
        """A URL containing ``/Device`` must be routed to get_device_bundle."""
        response = stub.get(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Bundle"
        # Verify Device resources were returned
        assert len(body["entry"]) == 1
        assert body["entry"][0]["resource"]["resourceType"] == "Device"

    def test_endpoint_url_returns_endpoint_bundle(self, stub: SdsFhirApiStub) -> None:
        """A URL containing ``/Endpoint`` must be routed to get_endpoint_bundle."""
        response = stub.get(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Bundle"
        # Verify Endpoint resources returned
        for entry in body["entry"]:
            assert entry["resource"]["resourceType"] == "Endpoint"

    def test_get_records_last_url(self, stub: SdsFhirApiStub) -> None:
        """The stub must record the last URL it was called with."""
        stub.get(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert stub.get_url == _BASE_DEVICE_URL

    def test_get_records_last_headers(self, stub: SdsFhirApiStub) -> None:
        """The stub must record the last headers it was called with."""
        headers = {"apikey": "test-key", "X-Correlation-Id": _VALID_CORRELATION_ID}
        stub.get(
            url=_BASE_DEVICE_URL,
            headers=headers,
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert stub.get_headers == headers

    def test_get_records_last_params(self, stub: SdsFhirApiStub) -> None:
        """The stub must record the last query params it was called with."""
        params = {"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM}
        stub.get(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params=params,
        )
        assert stub.get_params == params

    def test_get_records_last_timeout(self, stub: SdsFhirApiStub) -> None:
        """The stub must record the last timeout value it was called with."""
        stub.get(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
            timeout=30,
        )
        assert stub.get_timeout == 30


# ---------------------------------------------------------------------------
# upsert_device / upsert_endpoint – dynamic data management
# ---------------------------------------------------------------------------


class TestUpsertOperations:
    """Verify that devices and endpoints can be dynamically added to the stub."""

    def test_upsert_device_is_returned_by_get_device_bundle(
        self, stub: SdsFhirApiStub
    ) -> None:
        """A device added via upsert_device must be returned in subsequent queries."""
        stub.clear_devices()
        new_device: dict[str, object] = {
            "resourceType": "Device",
            "id": "new-device-123",
            "identifier": [],
            "owner": {
                "identifier": {"system": FHIRSystem.ODS_CODE, "value": "NEW_ORG"}
            },
        }
        stub.upsert_device(
            organization_ods="NEW_ORG",
            service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            device=new_device,
        )

        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={
                "organization": f"{FHIRSystem.ODS_CODE}|NEW_ORG",
                "identifier": _INTERACTION_ID_PARAM,
            },
        )
        body = response.json()
        assert body["total"] == 1
        assert body["entry"][0]["resource"]["id"] == "new-device-123"

    def test_clear_devices_removes_all_devices(self, stub: SdsFhirApiStub) -> None:
        """After clear_devices, all Device queries must return an empty Bundle."""
        stub.clear_devices()

        response = stub.get_device_bundle(
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["total"] == 0

    def test_upsert_endpoint_is_returned_by_get_endpoint_bundle(
        self, stub: SdsFhirApiStub
    ) -> None:
        """An endpoint added via upsert_endpoint must be returned in subsequent
        queries."""
        stub.clear_endpoints()
        new_asid = "999000000001"
        new_endpoint: dict[str, object] = {
            "resourceType": "Endpoint",
            "id": "new-endpoint-456",
            "status": "active",
            "connectionType": {
                "system": SdsFhirApiStub.CONNECTION_SYSTEM,
                "code": "hl7-fhir-rest",
                "display": SdsFhirApiStub.CONNECTION_DISPLAY,
            },
            "payloadType": [{"coding": [{"system": SdsFhirApiStub.CODING_SYSTEM}]}],
            "address": "https://new.example.com/fhir",
            "managingOrganization": {
                "identifier": {"system": FHIRSystem.ODS_CODE, "value": "NEW_ORG"}
            },
            "identifier": [{"system": FHIRSystem.NHS_SPINE_ASID, "value": new_asid}],
        }
        stub.upsert_endpoint(
            organization_ods="NEW_ORG",
            service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            endpoint=new_endpoint,
        )

        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={
                "organization": f"{FHIRSystem.ODS_CODE}|NEW_ORG",
                "identifier": _INTERACTION_ID_PARAM,
            },
        )
        body = response.json()
        assert body["total"] == 1
        assert body["entry"][0]["resource"]["id"] == "new-endpoint-456"

    def test_clear_endpoints_removes_all_endpoints(self, stub: SdsFhirApiStub) -> None:
        """After clear_endpoints, all Endpoint queries must return an empty Bundle."""
        stub.clear_endpoints()

        response = stub.get_endpoint_bundle(
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["total"] == 0
