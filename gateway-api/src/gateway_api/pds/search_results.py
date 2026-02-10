"""PDS search result data structures."""

from dataclasses import dataclass


@dataclass
class PdsSearchResults:
    """
    A single extracted patient record.

    Only a small subset of the PDS Patient fields are currently required by this
    gateway. More will be added in later phases.

    :param given_names: Given names from the *current* ``Patient.name`` record,
        concatenated with spaces.
    :param family_name: Family name from the *current* ``Patient.name`` record.
    :param nhs_number: NHS number (``Patient.id``).
    :param gp_ods_code: The ODS code of the *current* GP, extracted from
        ``Patient.generalPractitioner[].identifier.value`` if a current GP record exists
        otherwise ``None``.
    """

    given_names: str
    family_name: str
    nhs_number: str
    gp_ods_code: str | None
