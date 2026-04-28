import json
from pathlib import Path
from typing import Any


def _path_to_here() -> Path:
    return Path(__file__).parent


class Patients:
    @staticmethod
    def load_patient(filename: str) -> dict[str, Any]:
        with open(_path_to_here() / filename, encoding="utf-8") as f:
            patient: dict[str, Any] = json.load(f)
        return patient

    JANE_SMITH_9000000009 = load_patient("jane_smith_9000000009.json")
    NO_SDS_RESULT_9000000010 = load_patient("no_sds_result_9000000010.json")
    BLANK_ASID_SDS_RESULT_9000000011 = load_patient(
        "blank_asid_sds_result_9000000011.json"
    )
    INDUCE_PROVIDER_ERROR_9000000012 = load_patient(
        "induce_provider_error_9000000012.json"
    )
    BLANK_ENDPOINT_SDS_RESULT_9000000013 = load_patient(
        "blank_endpoint_sds_result_9000000013.json"
    )
    ALICE_JONES_9999999999 = load_patient("alice_jones_9999999999.json")
    ORANGE_BOX_TRIGGER_9690937278 = load_patient("orange_box_trigger_9690937278.json")
    LESTER_EGAN_9692140466 = load_patient("lester_egan_9692140466.json")
