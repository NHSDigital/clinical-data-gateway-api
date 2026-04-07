from dataclasses import dataclass


@dataclass(frozen=True)
class HumanName:
    family: str
    given: list[str] | None = None
    prefix: list[str] | None = None
