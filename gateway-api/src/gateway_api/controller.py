"""
Controller layer for orchestrating calls to external services
"""

import json
from typing import Any

from fhir.r4 import Device, Organization, Practitioner
from requests import Response

from gateway_api.clinical_jwt import JWT
from gateway_api.common.error import (
    NoAsidFoundError,
    NoCurrentEndpointError,
    NoCurrentProviderError,
    NoOrganisationFoundError,
)
from gateway_api.get_structured_record.request import GetStructuredRecordRequest
from gateway_api.pds import PdsClient
from gateway_api.provider import GpProviderClient
from gateway_api.sds import SdsClient, SdsSearchResults


class Controller:
    """
    Orchestrates calls to PDS -> SDS -> GP provider.
    """

    gp_provider_client: GpProviderClient | None

    def __init__(
        self,
        pds_base_url: str = PdsClient.SANDBOX_URL,
        sds_base_url: str = SdsClient.SANDBOX_URL,
        timeout: int = 10,
    ) -> None:
        """
        Create a controller instance.
        """
        self.pds_base_url = pds_base_url
        self.sds_base_url = sds_base_url
        self.timeout = timeout
        self.gp_provider_client = None

    def run(self, request: GetStructuredRecordRequest) -> Response:
        """
        Controller entry point

        Expects a GetStructuredRecordRequest instance that contains the header and body
        details of the HTTP request received

        Orchestration steps:
        1) Call PDS to obtain the patient's GP (provider) ODS code.
        2) Call SDS using provider ODS to obtain provider ASID + provider endpoint.
        3) Call SDS using consumer ODS to obtain consumer ASID.
        4) Call GP provider to obtain patient records.
        """
        auth_token = self.get_auth_token()

        provider_ods = self._get_pds_details(auth_token, request.nhs_number)

        consumer_asid, provider_asid, provider_endpoint = self._get_sds_details(
            request.ods_from.strip(), provider_ods
        )

        # TODO: De-ai-ify this comment
        # Extract CDG-specific identity fields from the FHIR Parameters before
        # forwarding. These fields are not part of the GP Connect spec and must
        # not be sent to the provider. They are provided as a parameter named
        # "identity" within the "parameter" array, with sub-items in "part":
        #   - "issuer"                 → string value in the "value" key
        #   - "requestingDevice"       → remainder of the identity part object
        #   - "requestingPractitioner" → remainder of the identity part object
        request_body: dict[str, Any] = json.loads(request.request_body)

        parameters: list[dict[str, Any]] = request_body.get("parameter", [])
        identity_param: dict[str, Any] | None = next(
            (p for p in parameters if p.get("name") == "identity"), None
        )
        request_body["parameter"] = [
            p for p in parameters if p.get("name") != "identity"
        ]

        identity_items: list[dict[str, Any]] = (
            identity_param.get("part", []) if identity_param else []
        )
        cdg_identity: dict[str, dict[str, Any]] = {
            item["name"]: item for item in identity_items if "name" in item
        }

        issuer_item = cdg_identity.get("issuer")
        issuer: str | None = issuer_item.get("value") if issuer_item else None

        requesting_device_item = cdg_identity.get("requestingDevice")
        if not requesting_device_item:
            # TODO: Handle this better, return correct http error
            raise ValueError("Missing 'requestingDevice' in identity in request body")

        requesting_device: Device = Device.model_validate(
            {k: v for k, v in requesting_device_item.items() if k != "name"}
        )

        requesting_practitioner_item = cdg_identity.get("requestingPractitioner")
        if not requesting_practitioner_item:
            # TODO: Handle this better, return correct http error
            raise ValueError(
                "Missing 'requestingPractitioner' in identity in request body"
            )

        requesting_practitioner: Practitioner = Practitioner.model_validate(
            {k: v for k, v in requesting_practitioner_item.items() if k != "name"}
        )

        if (
            issuer is None
            or requesting_device is None
            or requesting_practitioner is None
        ):
            # TODO: Handle this better, return all missing fields, return correct
            # http error
            raise ValueError(
                "Missing 'issuer', 'requestingDevice', or 'requestingPractitioner'"
                " parameter in request body"
            )

        forwarded_request_body = json.dumps(request_body)

        token = self.get_jwt_for_provider(
            provider_endpoint=provider_endpoint,
            consumer_ods=request.ods_from.strip(),
            issuer=issuer,
            requesting_device=requesting_device,
            requesting_practitioner=requesting_practitioner,
        )

        # Call GP provider with correct parameters
        self.gp_provider_client = GpProviderClient(
            provider_endpoint=provider_endpoint,
            provider_asid=provider_asid,
            consumer_asid=consumer_asid,
            token=token,
        )

        provider_response = self.gp_provider_client.access_structured_record(
            trace_id=request.trace_id,
            body=forwarded_request_body,
        )

        return provider_response

    def get_auth_token(self) -> str:
        """
        Retrieve the authorization token.

        This is a placeholder implementation. Replace with actual logic to obtain
        the auth token as needed.
        """
        return "AUTH_TOKEN123"

    def get_jwt_for_provider(
        self,
        provider_endpoint: str,
        consumer_ods: str,
        issuer: str,
        requesting_device: Device,
        requesting_practitioner: Practitioner,
    ) -> JWT:
        # For requesting device details, see:
        # https://webarchive.nationalarchives.gov.uk/ukgwa/20250307092533/https://developer.nhs.uk/apis/gpconnect/integration_cross_organisation_audit_and_provenance.html#requesting_device-claim
        # For requesting practitioner details, see:
        # https://webarchive.nationalarchives.gov.uk/ukgwa/20250307092533/https://developer.nhs.uk/apis/gpconnect/integration_cross_organisation_audit_and_provenance.html#requesting_practitioner-claim

        # requesting_device = Device.model_validate(
        #     {
        #         "resourceType": "Device",
        #         "identifier": [
        #             {
        #                 "system": "https://orange.testlab.nhs.uk/gpconnect-demonstrator/Id/local-system-instance-id",
        #                 "value": "gpcdemonstrator-1-orange",
        #             }
        #         ],
        #         "model": "GP Connect Demonstrator",
        #         "version": "1.5.0",
        #     }
        # )

        # # TODO [GPCAPIM-309]: Get practitioner details
        # requesting_practitioner = Practitioner.model_validate(
        #     {
        #         "resourceType": "Practitioner",
        #         "id": "10019",
        #         "name": [
        #             {
        #                 "family": "Doe",
        #                 "given": ["John"],
        #                 "prefix": ["Mr"],
        #             }
        #         ],
        #         "identifier": [
        #             {
        #                 "system": "https://fhir.nhs.uk/Id/sds-user-id",
        #                 "value": "111222333444",
        #             },
        #             {
        #                 "system": "https://fhir.nhs.uk/Id/sds-role-profile-id",
        #                 "value": "444555666777",
        #             },
        #             {
        #                 "system": "https://orange.testlab.nhs.uk/gpconnect-demonstrator/Id/local-user-id",
        #                 "value": "98ed4f78-814d-4266-8d5b-cde742f3093c",
        #             },
        #         ],
        #     }
        # )

        # TODO [GPCAPIM-363]: Get the consumer org name
        requesting_organization = Organization.from_ods_code(
            name="Consumer organisation name", ods_code=consumer_ods
        )

        # TODO [GPCAPIM-364]: Get consumer URL for issuer. Use CDG API URL for now.
        # issuer = "https://clinical-data-gateway-api.sandbox.nhs.uk"
        audience = provider_endpoint

        token = JWT(
            issuer=issuer,
            subject=requesting_practitioner.id,
            audience=audience,
            requesting_device=requesting_device.model_dump(),
            requesting_organization=requesting_organization.model_dump(),
            requesting_practitioner=requesting_practitioner.model_dump(),
        )
        return token

    def _get_pds_details(self, auth_token: str, nhs_number: str) -> str:
        """
        Call PDS to find the provider ODS code (GP ODS code) for a patient.
        """
        # PDS: find patient and extract GP ODS code (provider ODS)
        pds = PdsClient(
            auth_token=auth_token,
            base_url=self.pds_base_url,
            timeout=self.timeout,
            ignore_dates=True,
        )

        patient = pds.search_patient_by_nhs_number(nhs_number)

        if not patient.gp_ods_code:
            raise NoCurrentProviderError(nhs_number=nhs_number)

        return patient.gp_ods_code

    def _get_sds_details(
        self, consumer_ods: str, provider_ods: str
    ) -> tuple[str, str, str]:
        """
        Call SDS to obtain consumer ASID, provider ASID, and provider endpoint.

        This method performs two SDS lookups:
        - provider details (ASID + endpoint)
        - consumer details (ASID)
        """
        # SDS: Get provider details (ASID + endpoint) for provider ODS
        sds = SdsClient(
            base_url=self.sds_base_url,
            timeout=self.timeout,
        )

        provider_details: SdsSearchResults = sds.get_org_details(
            provider_ods, get_endpoint=True
        )
        if provider_details.is_not_found:
            raise NoOrganisationFoundError(org_type="provider", ods_code=provider_ods)

        provider_asid = (provider_details.asid or "").strip()
        if not provider_asid:
            raise NoAsidFoundError(org_type="provider", ods_code=provider_ods)

        provider_endpoint = (provider_details.endpoint or "").strip()
        if not provider_endpoint:
            raise NoCurrentEndpointError(provider_ods=provider_ods)

        # SDS: Get consumer details (ASID) for consumer ODS
        consumer_details: SdsSearchResults = sds.get_org_details(
            consumer_ods, get_endpoint=False
        )
        if consumer_details.is_not_found:
            raise NoOrganisationFoundError(org_type="consumer", ods_code=consumer_ods)

        consumer_asid = (consumer_details.asid or "").strip()
        if not consumer_asid:
            raise NoAsidFoundError(org_type="consumer", ods_code=consumer_ods)

        return consumer_asid, provider_asid, provider_endpoint
