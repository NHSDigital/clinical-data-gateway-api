from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Organization:
    ods_code: str
    name: str

    def to_dict(self) -> dict[str, Any]:
        """
        Return the Organization as a dictionary suitable for JWT payload.
        """
        return {
            "resourceType": "Organization",
            "identifier": [
                {
                    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                    "value": self.ods_code,
                }
            ],
            "name": self.name,
        }

    @property
    def json(self) -> dict[str, Any]:
        """
        Return the Organization as a dictionary suitable for JWT payload.
        Provided for backwards compatibility.
        """
        return self.to_dict()

    def __str__(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)
