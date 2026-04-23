from typing import Any

from stubs.data.patients import Patients


class Bundles:
    @staticmethod
    def _wrap_patient_in_bundle(patient: dict[str, Any]) -> dict[str, Any]:
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "meta": {
                "profile": [
                    "https://fhir.nhs.uk/STU3/StructureDefinition/GPConnect-StructuredRecord-Bundle-1"
                ]
            },
            "entry": [{"resource": patient}],
        }

    ALICE_JONES_9999999999 = _wrap_patient_in_bundle(Patients.ALICE_JONES_9999999999)
    INT_9658218865 = _wrap_patient_in_bundle(Patients.INT_9658218865)
