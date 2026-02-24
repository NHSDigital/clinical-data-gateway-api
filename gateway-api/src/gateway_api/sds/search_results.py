from dataclasses import dataclass


@dataclass
class SdsSearchResults:
    """
    Stub SDS search results dataclass.

    Replace this with the real one once it's implemented.
    """

    asid: str | None
    endpoint: str | None

    @property
    def is_not_found(self) -> bool:
        return self.asid is None and self.endpoint is None
