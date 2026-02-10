from dataclasses import dataclass


@dataclass
class SdsSearchResults:
    """
    Stub SDS search results dataclass.

    Replace this with the real one once it's implemented.

    :param asid: Accredited System ID.
    :param endpoint: Endpoint URL associated with the organisation, if applicable.
    """

    asid: str
    endpoint: str | None
