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
