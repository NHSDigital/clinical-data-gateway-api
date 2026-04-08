from typing import Annotated

from pydantic import BaseModel, Field, SerializeAsAny

from fhir import Resource


class Entry(BaseModel):
    full_url: str = Field(..., alias="fullUrl", frozen=True)
    resource: Annotated[SerializeAsAny[Resource], Field(frozen=True)]
