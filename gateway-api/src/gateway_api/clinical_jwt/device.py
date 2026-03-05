from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Device:
    system: str
    value: str
    model: str
    version: str

    def to_dict(self) -> dict[str, Any]:
        """
        Return the Device as a dictionary suitable for JWT payload.
        """
        return {
            "resourceType": "Device",
            "identifier": [{"system": self.system, "value": self.value}],
            "model": self.model,
            "version": self.version,
        }

    @property
    def json(self) -> dict[str, Any]:
        """
        Return the Device as a dictionary suitable for JWT payload.
        Provided for backwards compatibility.
        """
        return self.to_dict()

    def __str__(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)
