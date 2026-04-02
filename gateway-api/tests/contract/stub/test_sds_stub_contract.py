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
_PARTY_KEY_PROVIDER = f"{FHIRSystem.NHS_MHS_PARTY_KEY}|PROVIDER-0000806"

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

    def test_status_code_is_200(self, stub: SdsFhirApiStub) -> None:
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200

    def test_content_type_is_fhir_json(self, stub: SdsFhirApiStub) -> None:
        """The spec mandates ``application/fhir+json`` on every response."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert "application/fhir+json" in response.headers["Content-Type"]

    def test_response_body_resource_type_is_bundle(self, stub: SdsFhirApiStub) -> None:
        """The response body must be a FHIR Bundle resource."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["resourceType"] == "Bundle"

    def test_response_body_bundle_type_is_searchset(self, stub: SdsFhirApiStub) -> None:
        """The SDS spec requires Bundle.type to be ``searchset``."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["type"] == "searchset"

    def test_response_bundle_total_matches_entry_count(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Bundle.total must match the number of entries returned."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["total"] == len(body["entry"])

    def test_response_bundle_entry_has_full_url(self, stub: SdsFhirApiStub) -> None:
        """Each entry in the Bundle must have a ``fullUrl`` field."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert len(body["entry"]) >= 1  # sanity check for non-empty entries
        for entry in body["entry"]:
            assert "fullUrl" in entry
            assert entry["fullUrl"]  # non-empty

    def test_response_bundle_entry_full_url_contains_device_id(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The ``fullUrl`` must contain the Device resource ID."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            device_id = entry["resource"]["id"]
            assert device_id in entry["fullUrl"]

    def test_response_bundle_entry_has_search_mode_match(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Each entry must have ``search.mode`` set to ``match``."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert entry["search"]["mode"] == "match"

    def test_x_correlation_id_echoed_back_when_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The spec states ``X-Correlation-Id`` is mirrored back in the response."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key", "X-Correlation-Id": _VALID_CORRELATION_ID},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

    def test_x_correlation_id_absent_when_not_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``X-Correlation-Id`` must not appear in the response when not supplied."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert "X-Correlation-Id" not in response.headers

    def test_empty_bundle_returned_for_unknown_org(self, stub: SdsFhirApiStub) -> None:
        """An unknown organisation must return a 200 with an empty Bundle."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
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

    def test_query_with_party_key_returns_matching_device(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Including a party key identifier should still return a match."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={
                "organization": _ORG_PROVIDER,
                "identifier": [_INTERACTION_ID_PARAM, _PARTY_KEY_PROVIDER],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1


# ---------------------------------------------------------------------------
# GET /Device – Device resource structure
# ---------------------------------------------------------------------------


class TestGetDeviceResourceStructure:
    """Contract tests verifying the shape of returned Device resources."""

    def test_device_resource_type_is_device(self, stub: SdsFhirApiStub) -> None:
        """Each resource inside the Bundle must have ``resourceType: "Device"``."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert entry["resource"]["resourceType"] == "Device"

    def test_device_has_id(self, stub: SdsFhirApiStub) -> None:
        """Each Device resource must have an ``id`` field."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "id" in entry["resource"]
            assert entry["resource"]["id"]  # non-empty

    def test_device_has_identifier_list(self, stub: SdsFhirApiStub) -> None:
        """Each Device resource must have an ``identifier`` list."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert isinstance(entry["resource"]["identifier"], list)
            assert len(entry["resource"]["identifier"]) >= 1

    def test_device_identifier_contains_asid(self, stub: SdsFhirApiStub) -> None:
        """Device identifier must include an ASID entry."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            identifiers = entry["resource"]["identifier"]
            asid_entries = [
                i for i in identifiers if i.get("system") == FHIRSystem.NHS_SPINE_ASID
            ]
            assert len(asid_entries) >= 1

    def test_device_identifier_contains_party_key(self, stub: SdsFhirApiStub) -> None:
        """Device identifier must include a party key entry."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            identifiers = entry["resource"]["identifier"]
            party_key_entries = [
                i
                for i in identifiers
                if i.get("system") == FHIRSystem.NHS_MHS_PARTY_KEY
            ]
            assert len(party_key_entries) >= 1

    def test_device_has_owner(self, stub: SdsFhirApiStub) -> None:
        """Each Device resource must have an ``owner`` field."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "owner" in entry["resource"]

    def test_device_owner_identifier_uses_ods_system(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Device.owner.identifier.system must be the ODS code system."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            owner = entry["resource"]["owner"]
            assert owner["identifier"]["system"] == FHIRSystem.ODS_CODE


# ---------------------------------------------------------------------------
# GET /Device – 400 validation errors
# ---------------------------------------------------------------------------


class TestGetDeviceBundleValidationErrors:
    """Contract tests for GET /Device → 400 when required inputs are missing."""

    def test_missing_apikey_returns_400(self, stub: SdsFhirApiStub) -> None:
        """The spec requires the ``apikey`` header; its absence must yield 400."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400

    def test_missing_organization_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``organization`` is a required query parameter for /Device."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400

    def test_missing_identifier_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``identifier`` is a required query parameter for /Device."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={"organization": _ORG_PROVIDER},
        )
        assert response.status_code == 400

    def test_identifier_without_interaction_id_returns_400(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``identifier`` must include nhsServiceInteractionId for /Device."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={
                "organization": _ORG_PROVIDER,
                "identifier": _PARTY_KEY_PROVIDER,  # party key only, no interaction ID
            },
        )
        assert response.status_code == 400

    def test_error_response_resource_type_is_operation_outcome(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Every error body must be an ``OperationOutcome``."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},  # missing apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"

    def test_error_response_has_non_empty_issue_list(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The OperationOutcome must have a non-empty ``issue`` list."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},  # missing apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert isinstance(body.get("issue"), list)
        assert len(body["issue"]) >= 1

    def test_error_response_issue_has_severity(self, stub: SdsFhirApiStub) -> None:
        """Each issue in the OperationOutcome must have a ``severity`` field."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},  # missing apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "severity" in body["issue"][0]

    def test_error_response_issue_has_code(self, stub: SdsFhirApiStub) -> None:
        """Each issue in the OperationOutcome must have a ``code`` field."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},  # missing apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "code" in body["issue"][0]

    def test_error_response_issue_has_diagnostics(self, stub: SdsFhirApiStub) -> None:
        """Each issue must have a non-empty ``diagnostics`` string."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={},  # missing apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "diagnostics" in body["issue"][0]
        assert body["issue"][0]["diagnostics"]  # non-empty

    def test_missing_apikey_echoes_correlation_id(self, stub: SdsFhirApiStub) -> None:
        """``X-Correlation-Id`` must be echoed even in error responses."""
        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"X-Correlation-Id": _VALID_CORRELATION_ID},  # no apikey
            params={"organization": _ORG_PROVIDER, "identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID


# ---------------------------------------------------------------------------
# GET /Endpoint – 200 successful retrieval
# ---------------------------------------------------------------------------


class TestGetEndpointBundleSuccess:
    """Contract tests for the happy-path GET /Endpoint → 200 response."""

    def test_status_code_is_200(self, stub: SdsFhirApiStub) -> None:
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 200

    def test_content_type_is_fhir_json(self, stub: SdsFhirApiStub) -> None:
        """The spec mandates ``application/fhir+json`` on every response."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert "application/fhir+json" in response.headers["Content-Type"]

    def test_response_body_resource_type_is_bundle(self, stub: SdsFhirApiStub) -> None:
        """The response body must be a FHIR Bundle resource."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["resourceType"] == "Bundle"

    def test_response_body_bundle_type_is_searchset(self, stub: SdsFhirApiStub) -> None:
        """The SDS spec requires Bundle.type to be ``searchset``."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["type"] == "searchset"

    def test_response_bundle_total_matches_entry_count(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Bundle.total must match the number of entries returned."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["total"] == len(body["entry"])

    def test_response_bundle_entry_has_full_url(self, stub: SdsFhirApiStub) -> None:
        """Each entry in the Bundle must have a ``fullUrl`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert len(body["entry"]) >= 1
        for entry in body["entry"]:
            assert "fullUrl" in entry
            assert entry["fullUrl"]  # non-empty

    def test_response_bundle_entry_full_url_contains_endpoint_id(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The ``fullUrl`` must contain the Endpoint resource ID."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            endpoint_id = entry["resource"]["id"]
            assert endpoint_id in entry["fullUrl"]

    def test_response_bundle_entry_has_search_mode_match(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Each entry must have ``search.mode`` set to ``match``."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        for entry in body["entry"]:
            assert entry["search"]["mode"] == "match"

    def test_query_with_party_key_returns_matching_endpoint(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Including a party key identifier should return matching Endpoint entries."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={
                "identifier": [_INTERACTION_ID_PARAM, _PARTY_KEY_PROVIDER],
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] >= 1

    def test_x_correlation_id_echoed_back_when_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The spec states ``X-Correlation-Id`` is mirrored back in the response."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key", "X-Correlation-Id": _VALID_CORRELATION_ID},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID

    def test_x_correlation_id_absent_when_not_provided(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``X-Correlation-Id`` must not appear in the response when not supplied."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert "X-Correlation-Id" not in response.headers

    def test_empty_bundle_returned_for_unknown_party_key(
        self, stub: SdsFhirApiStub
    ) -> None:
        """A party key not present in the stub must yield an empty Bundle."""
        unknown_party_key = f"{FHIRSystem.NHS_MHS_PARTY_KEY}|UNKNOWN-9999999"
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": unknown_party_key},
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
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert entry["resource"]["resourceType"] == "Endpoint"

    def test_endpoint_has_id(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint resource must have an ``id`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "id" in entry["resource"]
            assert entry["resource"]["id"]  # non-empty

    def test_endpoint_has_status_active(self, stub: SdsFhirApiStub) -> None:
        """The SDS spec requires ``Endpoint.status`` to be ``active``."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert entry["resource"]["status"] == "active"

    def test_endpoint_has_connection_type(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint must have a ``connectionType`` object."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "connectionType" in entry["resource"]

    def test_endpoint_connection_type_has_system_and_code(
        self, stub: SdsFhirApiStub
    ) -> None:
        """``connectionType`` must have ``system`` and ``code`` fields."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            ct = entry["resource"]["connectionType"]
            assert "system" in ct
            assert "code" in ct

    def test_endpoint_has_payload_type(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint must have a ``payloadType`` list."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert isinstance(entry["resource"]["payloadType"], list)
            assert len(entry["resource"]["payloadType"]) >= 1

    def test_endpoint_has_address(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint must have a non-empty ``address`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "address" in entry["resource"]
            assert entry["resource"]["address"]  # non-empty

    def test_endpoint_has_managing_organization(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint must have a ``managingOrganization`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert "managingOrganization" in entry["resource"]

    def test_endpoint_managing_organization_uses_ods_system(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Endpoint.managingOrganization.identifier.system must be the ODS code
        system."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            managing_org = entry["resource"]["managingOrganization"]
            assert managing_org["identifier"]["system"] == FHIRSystem.ODS_CODE

    def test_endpoint_has_identifier_list(self, stub: SdsFhirApiStub) -> None:
        """Each Endpoint resource must have an ``identifier`` list."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            assert isinstance(entry["resource"]["identifier"], list)
            assert len(entry["resource"]["identifier"]) >= 1

    def test_endpoint_identifier_contains_asid(self, stub: SdsFhirApiStub) -> None:
        """Endpoint identifier must include an ASID entry."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            identifiers = entry["resource"]["identifier"]
            asid_entries = [
                i for i in identifiers if i.get("system") == FHIRSystem.NHS_SPINE_ASID
            ]
            assert len(asid_entries) >= 1

    def test_endpoint_identifier_contains_party_key(self, stub: SdsFhirApiStub) -> None:
        """Endpoint identifier must include a party key entry."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        for entry in body["entry"]:
            identifiers = entry["resource"]["identifier"]
            party_key_entries = [
                i
                for i in identifiers
                if i.get("system") == FHIRSystem.NHS_MHS_PARTY_KEY
            ]
            assert len(party_key_entries) >= 1


# ---------------------------------------------------------------------------
# GET /Endpoint – 400 validation errors
# ---------------------------------------------------------------------------


class TestGetEndpointBundleValidationErrors:
    """Contract tests for GET /Endpoint → 400 when required inputs are missing."""

    def test_missing_apikey_returns_400(self, stub: SdsFhirApiStub) -> None:
        """The spec requires the ``apikey`` header; its absence must yield 400."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400

    def test_missing_identifier_returns_400(self, stub: SdsFhirApiStub) -> None:
        """``identifier`` is a required query parameter for /Endpoint."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={},
        )
        assert response.status_code == 400

    def test_error_response_resource_type_is_operation_outcome(
        self, stub: SdsFhirApiStub
    ) -> None:
        """Every error body must be an ``OperationOutcome``."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},  # missing apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"

    def test_error_response_has_non_empty_issue_list(
        self, stub: SdsFhirApiStub
    ) -> None:
        """The OperationOutcome must have a non-empty ``issue`` list."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},  # missing apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert isinstance(body.get("issue"), list)
        assert len(body["issue"]) >= 1

    def test_error_response_issue_has_severity(self, stub: SdsFhirApiStub) -> None:
        """Each issue in the OperationOutcome must have a ``severity`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},  # missing apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "severity" in body["issue"][0]

    def test_error_response_issue_has_code(self, stub: SdsFhirApiStub) -> None:
        """Each issue in the OperationOutcome must have a ``code`` field."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},  # missing apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "code" in body["issue"][0]

    def test_error_response_issue_has_diagnostics(self, stub: SdsFhirApiStub) -> None:
        """Each issue must have a non-empty ``diagnostics`` string."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={},  # missing apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        body = response.json()
        assert "diagnostics" in body["issue"][0]
        assert body["issue"][0]["diagnostics"]  # non-empty

    def test_missing_apikey_echoes_correlation_id(self, stub: SdsFhirApiStub) -> None:
        """``X-Correlation-Id`` must be echoed even in error responses."""
        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"X-Correlation-Id": _VALID_CORRELATION_ID},  # no apikey
            params={"identifier": _INTERACTION_ID_PARAM},
        )
        assert response.status_code == 400
        assert response.headers.get("X-Correlation-Id") == _VALID_CORRELATION_ID


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
        assert len(body["entry"]) >= 1
        for entry in body["entry"]:
            assert entry["resource"]["resourceType"] == "Device"

    def test_endpoint_url_returns_endpoint_bundle(self, stub: SdsFhirApiStub) -> None:
        """A URL containing ``/Endpoint`` must be routed to get_endpoint_bundle."""
        response = stub.get(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
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
            "owner": {"identifier": {"system": FHIRSystem.ODS_CODE, "value": "NEWORG"}},
        }
        stub.upsert_device(
            organization_ods="NEWORG",
            service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            party_key=None,
            device=new_device,
        )

        response = stub.get_device_bundle(
            url=_BASE_DEVICE_URL,
            headers={"apikey": "test-key"},
            params={
                "organization": f"{FHIRSystem.ODS_CODE}|NEWORG",
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
            url=_BASE_DEVICE_URL,
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
        new_party_key = "NEWORG-0000999"
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
                "identifier": {"system": FHIRSystem.ODS_CODE, "value": "NEWORG"}
            },
            "identifier": [
                {"system": FHIRSystem.NHS_MHS_PARTY_KEY, "value": new_party_key}
            ],
        }
        stub.upsert_endpoint(
            organization_ods="NEWORG",
            service_interaction_id=ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            party_key=new_party_key,
            endpoint=new_endpoint,
        )

        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={
                "identifier": f"{FHIRSystem.NHS_MHS_PARTY_KEY}|{new_party_key}",
            },
        )
        body = response.json()
        assert body["total"] == 1
        assert body["entry"][0]["resource"]["id"] == "new-endpoint-456"

    def test_clear_endpoints_removes_all_endpoints(self, stub: SdsFhirApiStub) -> None:
        """After clear_endpoints, all Endpoint queries must return an empty Bundle."""
        stub.clear_endpoints()

        response = stub.get_endpoint_bundle(
            url=_BASE_ENDPOINT_URL,
            headers={"apikey": "test-key"},
            params={"identifier": _PARTY_KEY_PROVIDER},
        )
        body = response.json()
        assert body["total"] == 0
