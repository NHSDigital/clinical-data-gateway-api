"""
In-memory SDS FHIR R4 API stub.

The stub does **not** implement the full SDS API surface, nor full FHIR validation.
"""

from __future__ import annotations

import json
from http.client import responses as http_responses
from typing import Any

from requests import Response
from requests.structures import CaseInsensitiveDict


def _create_response(
    status_code: int,
    headers: dict[str, str],
    json_data: dict[str, Any],
) -> Response:
    """
    Create a :class:`requests.Response` object for the stub.

    :param status_code: HTTP status code.
    :param headers: Response headers dictionary.
    :param json_data: JSON body data.
    :return: A :class:`requests.Response` instance.
    """
    response = Response()
    response.status_code = status_code
    response.headers = CaseInsensitiveDict(headers)
    response._content = json.dumps(json_data).encode("utf-8")  # noqa: SLF001
    response.encoding = "utf-8"
    # Set a reason phrase for HTTP error handling
    response.reason = http_responses.get(status_code, "Unknown")
    return response


class SdsFhirApiStub:
    """
    Minimal in-memory stub for the SDS FHIR API, implementing ``GET /Device``
    and ``GET /Endpoint``

    Contract elements modelled from the SDS OpenAPI spec:

    * ``/Device`` requires query params:
        - ``organization`` (required): ODS code with FHIR identifier prefix
        - ``identifier`` (required, repeatable): Service interaction ID and/or party key
        - ``manufacturing-organization`` (optional): Manufacturing org ODS code
    * ``/Endpoint`` requires query param:
        - ``identifier`` (required, repeatable): Service interaction ID and/or party key
        - ``organization`` (optional): ODS code with FHIR identifier prefix
    * ``X-Correlation-Id`` is optional and echoed back if supplied
    * ``apikey`` header is required (but any value accepted in stub mode)
    * Returns a FHIR Bundle with ``resourceType: "Bundle"`` and ``type: "searchset"``

    See:
        https://github.com/NHSDigital/spine-directory-service-api
    """

    ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
    INTERACTION_SYSTEM = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
    PARTYKEY_SYSTEM = "https://fhir.nhs.uk/Id/nhsMhsPartyKey"
    ASID_SYSTEM = "https://fhir.nhs.uk/Id/nhsSpineASID"
    CONNECTION_SYSTEM = "http://terminology.hl7.org/CodeSystem/endpoint-connection-type"
    CODING_SYSTEM = "http://terminology.hl7.org/CodeSystem/endpoint-payload-type"

    GP_CONNECT_INTERACTION = (
        "urn:nhs:names:services:gpconnect:fhir:rest:read:metadata-1"
    )
    CONNECTION_DISPLAY = "HL7 FHIR"

    def __init__(self) -> None:
        """
        Create a new stub instance.

        :param strict_validation: If ``True``, enforce required query parameters and
            apikey header. If ``False``, validation is relaxed.
        """
        # Internal store: (org_ods, interaction_id, party_key) -> list[device_resource]
        # party_key may be None if not specified
        self._devices: dict[tuple[str, str, str | None], list[dict[str, Any]]] = {}

        # Internal store for endpoints:
        #   (org_ods, interaction_id, party_key) -> list[endpoint_resource]
        # org_ods and/or interaction_id may be None since they're optional for
        # endpoint queries
        self._endpoints: dict[
            tuple[str | None, str | None, str | None], list[dict[str, Any]]
        ] = {}

        # Seed some deterministic examples matching common test scenarios
        self._seed_default_devices()
        self._seed_default_endpoints()

    def _seed_default_devices(self) -> None:
        """Seed the stub with some default Device records for testing."""
        self.upsert_device(
            organization_ods="PROVIDER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="PROVIDER-0000806",
            device={
                "resourceType": "Device",
                "id": "F0F0E921-92CA-4A88-A550-2DBB36F703AF",
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_PROV",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "PROVIDER-0000806",
                    },
                ],
                "owner": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "PROVIDER",
                    },
                    "display": "Example NHS Trust",
                },
            },
        )

        self.upsert_device(
            organization_ods="CONSUMER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="CONSUMER-0000807",
            device={
                "resourceType": "Device",
                "id": "C0C0E921-92CA-4A88-A550-2DBB36F703AF",
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_CONS",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "CONSUMER-0000807",
                    },
                ],
                "owner": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "CONSUMER",
                    },
                    "display": "Example Consumer Organisation",
                },
            },
        )

    def _seed_default_endpoints(self) -> None:
        """Seed the stub with some default Endpoint records for testing."""
        # Example 1: Endpoint for provider organization with GP Connect interaction
        self.upsert_endpoint(
            organization_ods="PROVIDER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="PROVIDER-0000806",
            endpoint={
                "resourceType": "Endpoint",
                "id": "E0E0E921-92CA-4A88-A550-2DBB36F703AF",
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
                "address": "https://provider.example.com/fhir",
                "managingOrganization": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "PROVIDER",
                    }
                },
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_PROV",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "PROVIDER-0000806",
                    },
                ],
            },
        )

        # Also seed endpoint with PSIS interaction for backwards compatibility
        self.upsert_endpoint(
            organization_ods="PROVIDER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="PROVIDER-0000806",
            endpoint={
                "resourceType": "Endpoint",
                "id": "E0E0E921-92CA-4A88-A550-2DBB36F703AF",
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
                "address": "https://provider.example.com/fhir",
                "managingOrganization": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "PROVIDER",
                    }
                },
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_PROV",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "PROVIDER-0000806",
                    },
                ],
            },
        )

        # Example 2: Endpoint for consumer organization with GP Connect interaction
        self.upsert_endpoint(
            organization_ods="CONSUMER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="CONSUMER-0000807",
            endpoint={
                "resourceType": "Endpoint",
                "id": "E1E1E921-92CA-4A88-A550-2DBB36F703AF",
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
                "address": "https://consumer.example.com/fhir",
                "managingOrganization": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "CONSUMER",
                    }
                },
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_CONS",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "CONSUMER-0000807",
                    },
                ],
            },
        )

        # Also seed endpoint with PSIS interaction for backwards compatibility
        self.upsert_endpoint(
            organization_ods="CONSUMER",
            service_interaction_id=self.GP_CONNECT_INTERACTION,
            party_key="CONSUMER-0000807",
            endpoint={
                "resourceType": "Endpoint",
                "id": "E1E1E921-92CA-4A88-A550-2DBB36F703AF",
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
                "address": "https://consumer.example.com/fhir",
                "managingOrganization": {
                    "identifier": {
                        "system": self.ODS_SYSTEM,
                        "value": "CONSUMER",
                    }
                },
                "identifier": [
                    {
                        "system": self.ASID_SYSTEM,
                        "value": "asid_CONS",
                    },
                    {
                        "system": self.PARTYKEY_SYSTEM,
                        "value": "CONSUMER-0000807",
                    },
                ],
            },
        )

    # ---------------------------
    # Public API for tests
    # ---------------------------

    def upsert_device(
        self,
        organization_ods: str,
        service_interaction_id: str,
        party_key: str | None,
        device: dict[str, Any],
    ) -> None:
        """
        Insert or append a Device record in the stub store.

        Multiple devices can be registered for the same query combination (they will
        all be returned in the Bundle.entry array).

        :param organization_ods: Organization ODS code.
        :param service_interaction_id: Service interaction ID.
        :param party_key: Optional MHS party key.
        :param device: Device resource dictionary.
        """
        key = (organization_ods, service_interaction_id, party_key)
        if key not in self._devices:
            self._devices[key] = []
        self._devices[key].append(device)

    def clear_devices(self) -> None:
        """Clear all Device records from the stub."""
        self._devices.clear()

    def upsert_endpoint(
        self,
        organization_ods: str | None,
        service_interaction_id: str | None,
        party_key: str | None,
        endpoint: dict[str, Any],
    ) -> None:
        """
        Insert or append an Endpoint record in the stub store.

        Multiple endpoints can be registered for the same query combination (they will
        all be returned in the Bundle.entry array).

        :param organization_ods: Organization ODS code (optional for endpoints).
        :param service_interaction_id: Service interaction ID (optional for endpoints).
        :param party_key: Optional MHS party key.
        :param endpoint: Endpoint resource dictionary.
        """
        key = (organization_ods, service_interaction_id, party_key)
        if key not in self._endpoints:
            self._endpoints[key] = []
        self._endpoints[key].append(endpoint)

    def clear_endpoints(self) -> None:
        """Clear all Endpoint records from the stub."""
        self._endpoints.clear()

    def get_device_bundle(
        self,
        url: str,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        headers: dict[str, str],
        params: dict[str, Any],
        timeout: int | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
    ) -> Response:
        """
        Implements ``GET /Device``.

        :param url: Request URL (expected to end with /Device).
        :param headers: Request headers. Must include ``apikey``.
            May include ``X-Correlation-Id``.
        :param params: Query parameters dictionary. Must include ``organization`` and
            ``identifier`` (list).
        :param timeout: Timeout (ignored by the stub).
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
        org_ods = self._extract_param_value(organization, self.ODS_SYSTEM)

        # Parse identifier list (can be string or list)
        # if isinstance(identifier, str):
        identifier_list = [identifier] if isinstance(identifier, str) else identifier
        # else:
        #     identifier_list = identifier

        service_interaction_id: str | None = None
        party_key: str | None = None

        for ident in identifier_list:
            if self.INTERACTION_SYSTEM in ident:
                service_interaction_id = self._extract_param_value(
                    ident, self.INTERACTION_SYSTEM
                )
            elif self.PARTYKEY_SYSTEM in ident:
                party_key = self._extract_param_value(ident, self.PARTYKEY_SYSTEM)

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
            party_key=party_key,
        )

        # Build FHIR Bundle response
        bundle = self._build_bundle(devices)

        return _create_response(status_code=200, headers=headers_out, json_data=bundle)

    def get_endpoint_bundle(
        self,
        url: str,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,  # noqa: ARG002 # NOSONAR S1172 (ignored in stub)
    ) -> Response:
        """
        Implements ``GET /Endpoint``.

        :param url: Request URL (expected to end with /Endpoint).
        :param headers: Request headers. Must include ``apikey`.
            May include ``X-Correlation-Id``.
        :param params: Query parameters dictionary. Must include ``identifier`` (list).
            ``organization`` is optional.
        :param timeout: Timeout (ignored by the stub).
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
            org_ods = self._extract_param_value(organization, self.ODS_SYSTEM)

        # Parse identifier list (can be string or list)
        if isinstance(identifier, str):
            identifier = [identifier]

        service_interaction_id: str | None = None
        party_key: str | None = None

        for ident in identifier or []:
            if self.INTERACTION_SYSTEM in ident:
                service_interaction_id = self._extract_param_value(
                    ident, self.INTERACTION_SYSTEM
                )
            elif self.PARTYKEY_SYSTEM in ident:
                party_key = self._extract_param_value(ident, self.PARTYKEY_SYSTEM)

        # Look up endpoints
        endpoints = self._lookup_endpoints(
            org_ods=org_ods,
            service_interaction_id=service_interaction_id,
            party_key=party_key,
        )

        # Build FHIR Bundle response
        bundle = self._build_endpoint_bundle(endpoints)

        return _create_response(status_code=200, headers=headers_out, json_data=bundle)

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
        if "/Endpoint" in url:
            return self.get_endpoint_bundle(
                url=url, headers=headers, params=params, timeout=timeout
            )
        return self.get_device_bundle(
            url=url, headers=headers, params=params, timeout=timeout
        )

    # ---------------------------
    # Internal helpers
    # ---------------------------

    def _lookup_devices(
        self, org_ods: str, service_interaction_id: str, party_key: str | None
    ) -> list[dict[str, Any]]:
        """
        Look up devices matching the query parameters.

        :param org_ods: Organization ODS code.
        :param service_interaction_id: Service interaction ID.
        :param party_key: Optional party key.
        :return: List of matching Device resources.
        """
        # Exact match with party key (or None)
        key = (org_ods, service_interaction_id, party_key)
        if key in self._devices:
            return list(self._devices[key])

        # If no party_key was provided (None), search for any entries with the
        # same org+interaction
        # This allows querying without knowing the party_key upfront
        if party_key is None:
            for stored_key, devices in self._devices.items():
                stored_org, stored_interaction, _ = stored_key
                if (
                    stored_org == org_ods
                    and stored_interaction == service_interaction_id
                ):
                    return list(devices)

        # If party_key was provided but no exact match, try without party key
        if party_key:
            key_without_party = (org_ods, service_interaction_id, None)
            if key_without_party in self._devices:
                return list(self._devices[key_without_party])

        return []

    def _lookup_endpoints(
        self,
        org_ods: str | None,
        service_interaction_id: str | None,
        party_key: str | None,
    ) -> list[dict[str, Any]]:
        """
        Look up endpoints matching the query parameters.

        For /Endpoint, the query combinations are more flexible:
        - organization + service_interaction_id + party_key
        - organization + party_key
        - organization + service_interaction_id
        - service_interaction_id + party_key

        :param org_ods: Organization ODS code (optional).
        :param service_interaction_id: Service interaction ID (optional).
        :param party_key: Optional party key.
        :return: List of matching Endpoint resources.
        """
        results = []

        # Try to find exact matches and partial matches
        for key, endpoints in self._endpoints.items():
            stored_org, stored_interaction, stored_party = key

            # Check if the query parameters match
            org_match = org_ods is None or stored_org is None or org_ods == stored_org
            interaction_match = (
                service_interaction_id is None
                or stored_interaction is None
                or service_interaction_id == stored_interaction
            )
            party_match = (
                party_key is None or stored_party is None or party_key == stored_party
            )

            # If all specified parameters match, include these endpoints
            if org_match and interaction_match and party_match:
                # But at least one must be non-None and match
                has_match = (
                    (org_ods and stored_org and org_ods == stored_org)
                    or (
                        service_interaction_id
                        and stored_interaction
                        and service_interaction_id == stored_interaction
                    )
                    or (party_key and stored_party and party_key == stored_party)
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

    @staticmethod
    def _error_response(
        status_code: int, headers: dict[str, str], message: str
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
        return _create_response(
            status_code=status_code, headers=dict(headers), json_data=body
        )
