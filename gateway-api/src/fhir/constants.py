from enum import StrEnum


class FHIRSystem(StrEnum):
    """
    Enum for FHIR identifier systems used in the clinical data gateway.
    """

    NHS_NUMBER = "https://fhir.nhs.uk/Id/nhs-number"
    ODS_CODE = "https://fhir.nhs.uk/Id/ods-organization-code"
    SDS_USER_ID = "https://fhir.nhs.uk/Id/sds-user-id"
    SDS_ROLE_PROFILE_ID = "https://fhir.nhs.uk/Id/sds-role-profile-id"
    NHS_SERVICE_INTERACTION_ID = "https://fhir.nhs.uk/Id/nhsServiceInteractionId"
    NHS_SPINE_ASID = "https://fhir.nhs.uk/Id/nhsSpineASID"
