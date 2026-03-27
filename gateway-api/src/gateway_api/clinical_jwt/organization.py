from dataclasses import dataclass
from typing import Any

from fhir.constants import FHIRSystem


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
                    "system": FHIRSystem.ODS_CODE,
                    "value": self.ods_code,
                }
            ],
            "name": self.name,
        }
