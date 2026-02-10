import json
import pathlib
from typing import Any


def _path_to_here() -> pathlib.Path:
    return pathlib.Path(__file__).parent


class Patients:
    @staticmethod
    def load_patient(filename: str) -> dict[str, Any]:
        with open(_path_to_here() / filename, encoding="utf-8") as f:
            patient: dict[str, Any] = json.load(f)
        return patient

    JANE_SMITH_9000000009 = load_patient("jane_smith_9000000009.json")

    ALICE_JONES_9999999999 = load_patient("alice_jones_9999999999.json")
