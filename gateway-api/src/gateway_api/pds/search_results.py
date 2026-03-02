"""PDS search result data structures."""

from dataclasses import dataclass


@dataclass
class PdsSearchResults:
    """
    A single extracted patient record.

    Only a small subset of the PDS Patient fields are currently required by this
    gateway. More will be added in later phases.
    """

    given_names: str
    family_name: str
    nhs_number: str
    gp_ods_code: str | None
