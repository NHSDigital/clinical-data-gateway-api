"""
In-memory SDS FHIR R4 API stub.

The stub does **not** implement the full SDS API surface, nor full FHIR validation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from fhir.constants import FHIRSystem
from gateway_api.get_structured_record import (
    ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
    SDS_SANDBOX_INTERACTION_ID,
)

from stubs.base_stub import GetStub, StubBase

if TYPE_CHECKING:
    from requests import Response


class SdsFhirApiStub(StubBase, GetStub):
    """
    Minimal in-memory stub for the SDS FHIR API, implementing ``GET /Device``
    and ``GET /Endpoint``

    Contract elements modelled from the SDS OpenAPI spec:

    * ``/Device`` requires query params:
        - ``organization`` (required): ODS code with FHIR identifier prefix
        - ``identifier`` (required, repeatable): Service interaction ID
        - ``manufacturing-organization`` (optional): Manufacturing org ODS code
    * ``/Endpoint`` requires query param:
        - ``identifier`` (required, repeatable): Service interaction ID
        - ``organization`` (optional): ODS code with FHIR identifier prefix
    * ``X-Correlation-Id`` is optional and echoed back if supplied
    * ``apikey`` header is required (but any value accepted in stub mode)
    * Returns a FHIR Bundle with ``resourceType: "Bundle"`` and ``type: "searchset"``

    See:
        https://github.com/NHSDigital/spine-directory-service-api
    """

    CONNECTION_SYSTEM = (
        "https://terminology.hl7.org/CodeSystem/endpoint-connection-type"
    )
    CODING_SYSTEM = "https://terminology.hl7.org/CodeSystem/endpoint-payload-type"
    CONNECTION_DISPLAY = "HL7 FHIR"

    def __init__(self) -> None:
        """
        Create a new stub instance.

        :param strict_validation: If ``True``, enforce required query parameters and
            apikey header. If ``False``, validation is relaxed.
        """
        # Internal store: (org_ods, interaction_id) -> list[device_resource]
        self._devices: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
            list
        )

        # Internal store for endpoints:
        #   (org_ods, interaction_id) -> list[endpoint_resource]
        # org_ods may be None since it's optional for
        # endpoint queries
        self._endpoints: defaultdict[
            tuple[str | None, str | None], list[dict[str, Any]]
        ] = defaultdict(list)

        # Seed some deterministic examples matching common test scenarios
        self._seed_default_devices()
        self._seed_default_endpoints()

        self._last_headers: dict[str, str] = {}
        self._last_params: dict[str, str] = {}
        self._last_url: str = ""
        self._last_timeout: int | None = None

    @property
    def get_headers(self) -> dict[str, str]:
        return self._last_headers

    @property
    def get_params(self) -> dict[str, str]:
        return self._last_params

    @property
    def get_url(self) -> str:
        return self._last_url

    @property
    def get_timeout(self) -> int | None:
        return self._last_timeout

    # ---------------------------
    # Public API for tests
    # ---------------------------

    def upsert_device(
        self,
        organization_ods: str,
        service_interaction_id: str,
        device: dict[str, Any],
    ) -> None:
        """
        Insert or append a Device record in the stub store.

        Multiple devices can be registered for the same query combination (they will
        all be returned in the Bundle.entry array).

        :param organization_ods: Organization ODS code.
        :param service_interaction_id: Service interaction ID.
        :param device: Device resource dictionary.
        """
        key = (organization_ods, service_interaction_id)
        self._devices[key].append(device)

    def clear_devices(self) -> None:
        """Clear all Device records from the stub."""
        self._devices.clear()

    def upsert_endpoint(
        self,
        organization_ods: str | None,
        service_interaction_id: str | None,
        endpoint: dict[str, Any],
    ) -> None:
        """
        Insert or append an Endpoint record in the stub store.

        Multiple endpoints can be registered for the same query combination (they will
        all be returned in the Bundle.entry array).

        :param organization_ods: Organization ODS code (optional for endpoints).
        :param service_interaction_id: Service interaction ID (optional for endpoints).
        :param endpoint: Endpoint resource dictionary.
        """
        key = (organization_ods, service_interaction_id)
        self._endpoints[key].append(endpoint)

    def clear_endpoints(self) -> None:
        """Clear all Endpoint records from the stub."""
        self._endpoints.clear()

    def get_device_bundle(
        self,
        headers: dict[str, str],
        params: dict[str, Any],
    ) -> Response:
        """
        Implements ``GET /Device``.

        :param headers: Request headers. Must include ``apikey``.
            May include ``X-Correlation-Id``.
        :param params: Query parameters dictionary. Must include ``organization`` and
            ``identifier`` (list).
        :return: A :class:`requests.Response` representing either:
            * ``200`` with Bundle JSON (may be empty)
            * ``400`` with error details for missing/invalid parameters
        """
        headers_out: dict[str, str] = {}

        # Echo correlation ID if provided
        correlation_id = headers.get("X-Correlation-Id")
        if correlation_id:
            headers_out["X-Correlation-Id"] = correlation_id

        # Validate apikey header
        if "apikey" not in headers:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="Missing required header: apikey",
            )

        # Always validate required query parameters (not just in strict mode)
        organization = params.get("organization")
        identifier = params.get("identifier")

        if not organization:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="Missing required query parameter: organization",
            )
        if not identifier:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="Missing required query parameter: identifier",
            )

        # Parse organization ODS code
        org_ods = self._extract_param_value(organization, FHIRSystem.ODS_CODE)

        # Parse identifier list (can be string or list)
        # if isinstance(identifier, str):
        identifier_list = [identifier] if isinstance(identifier, str) else identifier
        # else:
        #     identifier_list = identifier

        service_interaction_id: str | None = None

        for ident in identifier_list:
            if FHIRSystem.NHS_SERVICE_INTERACTION_ID in ident:
                service_interaction_id = self._extract_param_value(
                    ident, FHIRSystem.NHS_SERVICE_INTERACTION_ID
                )

        # Always validate service interaction ID is present
        if not service_interaction_id:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="identifier must include nhsServiceInteractionId",
            )

        # Look up devices
        devices = self._lookup_devices(
            org_ods=org_ods or "",
            service_interaction_id=service_interaction_id or "",
        )

        # Build FHIR Bundle response
        bundle = self._build_bundle(devices)

        return self._create_response(
            status_code=200, json_data=bundle, additional_headers=headers_out
        )

    def get_endpoint_bundle(
        self,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Response:
        """
        Implements ``GET /Endpoint``.

        :param headers: Request headers. Must include ``apikey``.
            May include ``X-Correlation-Id``.
        :param params: Query parameters dictionary. Must include ``identifier`` (list).
            ``organization`` is optional.
        :return: A :class:`requests.Response` representing either:
            * ``200`` with Bundle JSON (may be empty)
            * ``400`` with error details for missing/invalid parameters
        """
        headers = headers or {}
        params = params or {}

        headers_out: dict[str, str] = {}

        # Echo correlation ID if provided
        correlation_id = headers.get("X-Correlation-Id")
        if correlation_id:
            headers_out["X-Correlation-Id"] = correlation_id

        # Validate apikey header
        if "apikey" not in headers:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="Missing required header: apikey",
            )

        # Always validate required query parameters (not just in strict mode)
        identifier = params.get("identifier")
        organization = params.get("organization")

        if not identifier:
            return self._error_response(
                status_code=400,
                headers=headers_out,
                message="Missing required query parameter: identifier",
            )

        # Parse organization ODS code (optional)
        org_ods: str | None = None
        if organization:
            org_ods = self._extract_param_value(organization, FHIRSystem.ODS_CODE)

        # Parse identifier list (can be string or list)
        if isinstance(identifier, str):
            identifier = [identifier]

        service_interaction_id: str | None = None

        for ident in identifier or []:
            if FHIRSystem.NHS_SERVICE_INTERACTION_ID in ident:
                service_interaction_id = self._extract_param_value(
                    ident, FHIRSystem.NHS_SERVICE_INTERACTION_ID
                )

        # Look up endpoints
        endpoints = self._lookup_endpoints(
            org_ods=org_ods,
            service_interaction_id=service_interaction_id,
        )

        # Build FHIR Bundle response
        bundle = self._build_endpoint_bundle(endpoints)

        return self._create_response(
            status_code=200, json_data=bundle, additional_headers=headers_out
        )

    def get(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any],
        timeout: int = 10,
    ) -> Response:
        """
        Convenience method matching requests.get signature for easy monkeypatching.

        Routes to the appropriate handler based on the URL path.

        :param url: Request URL.
        :param headers: Request headers.
        :param params: Query parameters.
        :param timeout: Timeout value.
        :return: A :class:`requests.Response`.
        """
        self._last_url = url
        self._last_headers = headers
        self._last_params = params
        self._last_timeout = timeout

        # Only handling two endpoints. If it's not /Endpoint it's /Device.
        if "/Endpoint" in url:
            return self.get_endpoint_bundle(headers=headers, params=params)
        return self.get_device_bundle(headers=headers, params=params)

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _seed_default_devices(self) -> None:
        """Seed the stub with some default Device records for testing."""
        # Define test device data as a list of parameters
        device_data = [
            {
                "org_ods": "PROVIDER",
                "device_id": "F0F0E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "asid_PROV",
                "display": "Example NHS Trust",
            },
            {
                "org_ods": "CONSUMER",
                "device_id": "C0C0E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "210987654321",
                "display": "Example Consumer Organisation",
            },
            {
                "org_ods": "A12345",
                "device_id": "A1A1E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "asid_A12345",
                "display": "Example GP Practice A12345",
            },
            {
                "org_ods": "BlankAsidInSDS",
                "device_id": "1f453b59-3bc5-48ff-9835-3d9d0ef636ef",
                "asid": "",
                "display": "GP with blank ASID - testing error handling",
            },
            {
                "org_ods": "BlankEndpointInSDS",
                "device_id": "74b40e5d-d72a-4667-beb5-b15ae6b4e25d",
                "asid": "ASIDforGPWithoutEndpoint",
                "display": "GP with no provider endpoint - testing error handling",
            },
            {
                "org_ods": "S44444",
                "device_id": "B2B2E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "200000000359",
                "display": "Dummy ODS/ASID for Orange Box",
            },
            {
                "org_ods": "S55555",
                "device_id": "B3B3E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "918999198738",
                "display": "ODS/ASID triggering Orange Box",
            },
            {
                "org_ods": "EMIS_INT_ODS_CODE",
                "party_key": "EMIS_INT_ODS_CODE-0000809",
                "device_id": "5CF77971-5732-43C6-959B-90F0DB6E49AD",
                "asid": "200000000948",
                "display": "GP with endpoint to get to EMIS INT TEST",
            },
        ]

        # Seed each device for both interaction IDs so the stub works whether
        # the SdsClient is connecting to the sandbox (SANDBOX_INTERACTION_ID)
        # or a non-sandbox environment (ACCESS_RECORD_STRUCTURED_INTERACTION_ID).
        interaction_ids = [
            ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            SDS_SANDBOX_INTERACTION_ID,
        ]

        for data in device_data:
            for interaction_id in interaction_ids:
                self.upsert_device(
                    organization_ods=data["org_ods"],
                    service_interaction_id=interaction_id,
                    device=self._create_device_resource(
                        device_id=data["device_id"],
                        asid=data["asid"],
                        org_ods=data["org_ods"],
                        display=data["display"],
                    ),
                )

    def _seed_default_endpoints(self) -> None:
        """Seed the stub with some default Endpoint records for testing."""
        # Define test endpoint data as a list of parameters
        endpoint_data = [
            {
                "org_ods": "PROVIDER",
                "endpoint_id": "E0E0E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "asid_PROV",
                "address": "https://provider.example.com/fhir",
            },
            {
                "org_ods": "CONSUMER",
                "endpoint_id": "E1E1E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "210987654321",
                "address": "https://consumer.example.com/fhir",
            },
            {
                "org_ods": "A12345",
                "endpoint_id": "E2E2E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "asid_A12345",
                "address": "https://a12345.example.com/fhir",
            },
            {
                "org_ods": "S55555",
                "endpoint_id": "E3E3E921-92CA-4A88-A550-2DBB36F703AF",
                "asid": "918999198738",
                "address": "https://orange.testlab.nhs.uk/B82617/STU3/1/gpconnect/structured/fhir/",
            },
            {
                "org_ods": "EMIS_INT_ODS_CODE",
                "party_key": "EMIS_INT_ODS_CODE-0000809",
                "endpoint_id": "BD635368-97E0-4935-A0D7-55CFDE574C93",
                "asid": "200000000948",
                "address": "https://gpcassurance-b86047.emis.thirdparty.nhs.uk/A82038/STU3/1/GPConnect/structured",
            },
        ]

        # Seed each endpoint for both interaction IDs so the stub works whether
        # the SdsClient is connecting to the sandbox (SANDBOX_INTERACTION_ID)
        # or a non-sandbox environment (ACCESS_RECORD_STRUCTURED_INTERACTION_ID).
        interaction_ids = [
            ACCESS_RECORD_STRUCTURED_INTERACTION_ID,
            SDS_SANDBOX_INTERACTION_ID,
        ]

        for data in endpoint_data:
            for interaction_id in interaction_ids:
                self.upsert_endpoint(
                    organization_ods=data["org_ods"],
                    service_interaction_id=interaction_id,
                    endpoint=self._create_endpoint_resource(
                        endpoint_id=data["endpoint_id"],
                        asid=data["asid"],
                        org_ods=data["org_ods"],
                        address=data["address"],
                    ),
                )

    def _create_device_resource(
        self,
        device_id: str,
        asid: str,
        org_ods: str,
        display: str,
    ) -> dict[str, Any]:
        """Create a Device resource dictionary with the given parameters."""
        return {
            "resourceType": "Device",
            "id": device_id,
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": asid,
                },
            ],
            "owner": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": org_ods,
                },
                "display": display,
            },
        }

    def _create_endpoint_resource(
        self,
        endpoint_id: str,
        asid: str,
        org_ods: str,
        address: str,
    ) -> dict[str, Any]:
        """Create an Endpoint resource dictionary with the given parameters."""
        return {
            "resourceType": "Endpoint",
            "id": endpoint_id,
            "status": "active",
            "connectionType": {
                "system": self.CONNECTION_SYSTEM,
                "code": "hl7-fhir-rest",
                "display": self.CONNECTION_DISPLAY,
            },
            "payloadType": [
                {
                    "coding": [
                        {
                            "system": self.CODING_SYSTEM,
                            "code": "any",
                            "display": "Any",
                        }
                    ]
                }
            ],
            "address": address,
            "managingOrganization": {
                "identifier": {
                    "system": FHIRSystem.ODS_CODE,
                    "value": org_ods,
                }
            },
            "identifier": [
                {
                    "system": FHIRSystem.NHS_SPINE_ASID,
                    "value": asid,
                },
            ],
        }

    def _lookup_devices(
        self, org_ods: str, service_interaction_id: str
    ) -> list[dict[str, Any]]:
        """
        Look up devices matching the query parameters.

        :param org_ods: Organization ODS code.
        :param service_interaction_id: Service interaction ID.
        :return: List of matching Device resources.
        """
        key = (org_ods, service_interaction_id)
        if key in self._devices:
            return list(self._devices[key])
        return []

    def _lookup_endpoints(
        self,
        org_ods: str | None,
        service_interaction_id: str | None,
    ) -> list[dict[str, Any]]:
        """
        Look up endpoints matching the query parameters.

        For /Endpoint, the query combinations are:
        - organization + service_interaction_id

        :param org_ods: Organization ODS code (optional).
        :param service_interaction_id: Service interaction ID (optional).
        :return: List of matching Endpoint resources.
        """
        results = []

        # Try to find exact matches and partial matches
        for key, endpoints in self._endpoints.items():
            stored_org, stored_interaction = key

            # Check if the query parameters match
            org_match = org_ods is None or stored_org is None or org_ods == stored_org
            interaction_match = (
                service_interaction_id is None
                or stored_interaction is None
                or service_interaction_id == stored_interaction
            )

            # If all specified parameters match, include these endpoints
            if org_match and interaction_match:
                # But at least one must be non-None and match
                has_match = (org_ods and stored_org and org_ods == stored_org) or (
                    service_interaction_id
                    and stored_interaction
                    and service_interaction_id == stored_interaction
                )
                if has_match:
                    results.extend(endpoints)

        return results

    def _build_bundle(self, devices: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Build a FHIR Bundle from a list of Device resources.

        :param devices: List of Device resources.
        :return: FHIR Bundle dictionary.
        """
        entries = []
        for device in devices:
            device_id = device.get("id", "unknown")
            entries.append(
                {
                    "fullUrl": f"https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Device/{device_id}",
                    "resource": device,
                    "search": {"mode": "match"},
                }
            )

        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(devices),
            "entry": entries,
        }

    def _build_endpoint_bundle(self, endpoints: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Build a FHIR Bundle from a list of Endpoint resources.

        :param endpoints: List of Endpoint resources.
        :return: FHIR Bundle dictionary.
        """
        entries = []
        for endpoint in endpoints:
            endpoint_id = endpoint.get("id", "unknown")
            entries.append(
                {
                    "fullUrl": f"https://sandbox.api.service.nhs.uk/spine-directory/FHIR/R4/Endpoint/{endpoint_id}",
                    "resource": endpoint,
                    "search": {"mode": "match"},
                }
            )

        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": len(endpoints),
            "entry": entries,
        }

    @staticmethod
    def _extract_param_value(param: str, system: str) -> str | None:
        """
        Extract the value from a FHIR-style parameter like 'system|value'.

        :param param: Parameter string in format 'system|value'.
        :param system: Expected system URL.
        :return: The value part, or None if not found.
        """
        if not param or "|" not in param:
            return None

        parts = param.split("|", 1)
        if len(parts) != 2:
            return None

        param_system, param_value = parts
        if param_system == system:
            return param_value.strip()

        return None

    def _error_response(
        self, status_code: int, headers: dict[str, str], message: str
    ) -> Response:
        """
        Build an error response.

        :param status_code: HTTP status code.
        :param headers: Response headers.
        :param message: Error message.
        :return: A :class:`requests.Response` with error details.
        """
        body = {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "invalid",
                    "diagnostics": message,
                }
            ],
        }
        return self._create_response(
            status_code=status_code, json_data=body, additional_headers=dict(headers)
        )
