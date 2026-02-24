from dataclasses import dataclass


@dataclass(kw_only=True)
class Practitioner:
    id: str
    sds_userid: str
    role_profile_id: str
    userid_url: str
    userid_value: str
    family_name: str
    given_name: str | None = None
    prefix: str | None = None

    def __post_init__(self) -> None:
        given = "" if self.given_name is None else f',"given":["{self.given_name}"]'
        prefix = "" if self.prefix is None else f',"prefix":["{self.prefix}"]'
        self._name_str = f'[{{"family": "{self.family_name}"{given}{prefix}}}]'

    @property
    def json(self) -> str:
        user_id_system = "https://fhir.nhs.uk/Id/sds-user-id"
        role_id_system = "https://fhir.nhs.uk/Id/sds-role-profile-id"

        outstr = f"""
        "requesting_practitioner": {{
        "resourceType": "Practitioner",
        "id": "{self.id}",
        "identifier": [
        {{
            "system": "{user_id_system}",
            "value": "{self.sds_userid}"
        }},
        {{
            "system": "{role_id_system}",
            "value": "{self.role_profile_id}"
        }},
        {{
            "system": "{self.userid_url}",
            "value": "{self.userid_value}"
        }}
        ],
        "name": {self._name_str}
        }}
        """
        return outstr.strip()

    def __str__(self) -> str:
        return self.json
