from typing import Any

from pydantic import BaseModel, Field


# TODO: convert this to dataclass/ABC like the other elements?
class Reference(BaseModel):
    """A FHIR R4 Reference base class."""

    reference_type: str = Field(alias="type", frozen=True)

    def __init_subclass__(
        cls, reference_type: str, **kwargs: Any
    ) -> None:  # TODO: Why is this necessary?
        super().__init_subclass__(**kwargs)
