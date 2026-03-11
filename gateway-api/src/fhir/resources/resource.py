from typing import Annotated, Any, ClassVar, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidatorFunctionWrapHandler,
    field_validator,
    model_validator,
)

from ..elements.meta import Meta


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
