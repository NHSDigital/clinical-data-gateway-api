from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Device:
    system: str
    value: str
    model: str
    version: str

    @property
    def json(self) -> str:
        outstr = f"""
        {{
        "resourceType": "Device",
        "identifier": [
            {{
                "system": "{self.system}",
                "value": "{self.value}"
            }}
        ],
        "model": "{self.model}",
        "version": "{self.version}"
        }}
        """
        return outstr.strip()

    def __str__(self) -> str:
        return self.json
