from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializeAsAny,
    ValidatorFunctionWrapHandler,
    field_validator,
    model_validator,
)

from .elements import Identifier, Issue, Meta, UUIDIdentifier


class Resource(BaseModel):
    """A FHIR R4 Resource base class."""

    # class variable to hold class mappings per resource_type
    __resource_types: ClassVar[dict[str, type["Resource"]]] = {}
    __expected_resource_type: ClassVar[dict[type["Resource"], str]] = {}

    meta: Annotated[Meta | None, Field(alias="meta", frozen=True)] = None
    resource_type: str = Field(alias="resourceType", frozen=True)

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    def __init_subclass__(cls, resource_type: str, **kwargs: Any) -> None:
        cls.__resource_types[resource_type] = cls
        cls.__expected_resource_type[cls] = resource_type

        super().__init_subclass__(**kwargs)

    def model_dump_json(self, *args: Any, **kwargs: Any) -> str:
        # FHIR resources should not return empty fields
        kwargs.setdefault("exclude_none", True)
        return super().model_dump_json(*args, **kwargs)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        # FHIR resources should not return empty fields
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(*args, **kwargs)

    @model_validator(mode="wrap")
    @classmethod
    def validate_with_subtype(
        cls, value: dict[str, Any], handler: ValidatorFunctionWrapHandler
    ) -> Any:
        """
        Provides a model validator that instantiates the correct Resource subclass
        based on its defined resource_type.
        """
        # If we're not currently acting on a top level Resource, and we've not been
        # provided a generic dictonary object, delegate to the normal handler.
        if cls != Resource or not isinstance(value, dict):
            return handler(value)

        if "resourceType" not in value or value["resourceType"] is None:
            raise TypeError("resourceType is required for Resource validation.")

        resource_type = value["resourceType"]

        subclass = cls.__resource_types.get(resource_type)
        if subclass is None:
            raise TypeError(f"Unknown resource type: {resource_type}")

        # Instantiate the subclass using the dictionary values.
        return subclass.model_validate(value)

    @classmethod
    def create(cls, **kwargs: Any) -> Self:
        """
        Create a Resource instance with the correct resourceType.
        Note any unknown arguments provided via this method will only error at runtime.
        """
        return cls(resourceType=cls.__expected_resource_type[cls], **kwargs)

    @field_validator("resource_type", mode="after")
    @classmethod
    def _validate_resource_type(cls, value: str) -> str:
        expected_resource_type = cls.__expected_resource_type[cls]
        if value != expected_resource_type:
            raise ValueError(
                f"Resource type '{value}' does not match expected "
                f"resource type '{expected_resource_type}'."
            )
        return value


type BundleType = Literal["document", "transaction", "searchset", "collection"]


class Bundle(Resource, resource_type="Bundle"):
    """A FHIR R4 Bundle resource."""

    bundle_type: BundleType = Field(alias="type", frozen=True)
    identifier: Annotated[UUIDIdentifier | None, Field(frozen=True)] = None
    entries: list["Bundle.Entry"] | None = Field(None, frozen=True, alias="entry")

    class Entry(BaseModel):
        full_url: str = Field(..., alias="fullUrl", frozen=True)
        resource: Annotated[SerializeAsAny[Resource], Field(frozen=True)]

    def find_resources[T: Resource](self, t: type[T]) -> list[T]:
        """
        Find all resources of a given type in the bundle entries. If the bundle has no
        entries, an empty list is returned.
        Args:
            t: The resource type to search for.
        Returns:
            A list of resources of the specified type.
        """
        return [
            entry.resource
            for entry in self.entries or []
            if isinstance(entry.resource, t)
        ]

    @classmethod
    def empty(cls, bundle_type: BundleType) -> "Bundle":
        """Create an empty Bundle of the specified type."""
        return cls.create(type=bundle_type, entry=None)


class Device(Resource, resource_type="Device"):
    """A FHIR R4 Device resource."""

    class ASIDIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhsSpineASID"
    ):
        """A FHIR R4 ASID Identifier."""

    class PartyKeyIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhsMhsPartyKey"
    ):
        """A FHIR R4 Party Key Identifier."""

    identifier: Annotated[
        list[ASIDIdentifier | PartyKeyIdentifier], Field(frozen=True, min_length=1)
    ]


class Endpoint(Resource, resource_type="Endpoint"):
    """A FHIR R4 Endpoint resource."""

    address: str | None = Field(None, frozen=True)


class OperationOutcome(Resource, resource_type="OperationOutcome"):
    """A FHIR R4 OperationOutcome resource."""

    issue: Annotated[list[Issue], Field(frozen=True)]


class Reference(BaseModel):
    """A FHIR R4 Reference base class."""

    reference_type: str = Field(alias="type", frozen=True)

    def __init_subclass__(
        cls, reference_type: str, **kwargs: Any
    ) -> None:  # TODO: Why is this necessary?
        super().__init_subclass__(**kwargs)


class Patient(Resource, resource_type="Patient"):
    """A FHIR R4 Patient resource."""

    class PatientIdentifier(
        Identifier, expected_system="https://fhir.nhs.uk/Id/nhs-number"
    ):
        """A FHIR R4 Patient Identifier utilising the NHS Number system."""

        def __init__(self, value: str):
            super().__init__(value=value, system=self._expected_system)

        @classmethod
        def from_nhs_number(cls, nhs_number: str) -> "Patient.PatientIdentifier":
            """Create a PatientIdentifier from an NHS number."""
            return cls(value=nhs_number)

    identifier: Annotated[list[PatientIdentifier], Field(frozen=True, min_length=1)]

    @property
    def nhs_number(self) -> str:
        return self.identifier[0].value

    class GeneralPractitioner(Reference, reference_type="Organization"):
        class OrganizationIdentifier(
            Identifier, expected_system="https://fhir.nhs.uk/Id/ods-organization-code"
        ):
            """
            A FHIR R4 Organization Identifier utilising the ODS Organization Code
            system.
            """

        identifier: Annotated[OrganizationIdentifier, Field(frozen=True)]

    generalPractitioner: Annotated[
        list[GeneralPractitioner] | None, Field(frozen=True)
    ] = None

    @property
    def gp_ods_code(self) -> str | None:
        if not self.generalPractitioner:
            return None

        return self.generalPractitioner[0].identifier.value
