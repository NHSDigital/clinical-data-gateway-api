from dataclasses import dataclass
from typing import Any

from fhir.constants import FHIRSystem


@dataclass(frozen=True, kw_only=True)
class Practitioner:
    id: str
    sds_userid: str
    role_profile_id: str
    userid_url: str
    userid_value: str
    family_name: str
    given_name: str | None = None
    prefix: str | None = None

    def _build_name(self) -> list[dict[str, Any]]:
        """Build the name array with proper structure for JWT."""
        name_dict: dict[str, Any] = {"family": self.family_name}
        if self.given_name is not None:
            name_dict["given"] = [self.given_name]
        if self.prefix is not None:
            name_dict["prefix"] = [self.prefix]
        return [name_dict]

    def to_dict(self) -> dict[str, Any]:
        """
        Return the Practitioner as a dictionary suitable for JWT payload.
        """
        user_id_system = FHIRSystem.SDS_USER_ID
        role_id_system = FHIRSystem.SDS_ROLE_PROFILE_ID

        return {
            "resourceType": "Practitioner",
            "id": self.id,
            "identifier": [
                {"system": user_id_system, "value": self.sds_userid},
                {"system": role_id_system, "value": self.role_profile_id},
                {"system": self.userid_url, "value": self.userid_value},
            ],
            "name": self._build_name(),
        }
