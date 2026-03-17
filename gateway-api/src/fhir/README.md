# FHIR Types in Gateway API

## What is FHIR?

FHIR (Fast Healthcare Interoperability Resources) is the HL7 standard for exchanging healthcare information as structured resources over HTTP APIs.

Read more on the standards: [R4](https://hl7.org/fhir/R4/overview.html) and [STU3](https://hl7.org/fhir/STU3/overview.html).

In this codebase, the FHIR package provides strongly typed Python models for request validation, response parsing, and safe serialization.

## FHIR versions in Clinical Data Sharing APIs

Two FHIR versions are used:

- STU3: used only for inbound Gateway API operation messages with `resourceType` Parameters (the Access Record Structured request payload).
- R4: used for all other typed resources in this module, including PDS FHIR resources such as Patient.

Version behaviour in the current flow:

- Inbound request body is validated as STU3 Parameters.
- Outbound provider response body is returned without transformation (mirrored payload).
- PDS, SDS, and internal typed handling use R4 resource models.

## How Pydantic is used

This package uses Pydantic to make FHIR payload handling explicit and safe:

- Model validation: model_validate(...) is used to parse inbound JSON into typed models.
- Field aliasing: FHIR JSON names like `resourceType`, `fullUrl`, `lastUpdated` are mapped with `Field(alias=...)`.
- Type constraints: `Annotated`, `Literal`, and `min_length` constraints enforce schema-like rules.
- Runtime guards: validators check that `resourceType` and identifier system values match expected FHIR semantics.
- Polymorphism: the Resource base type dispatches to the correct subclass from `resourceType`.
- Serialization: `model_dump()`/`model_dump_json()` default to exclude_none=True to avoid emitting empty FHIR fields.

Typical patterns in this code:

- Parse JSON from API input or upstream systems into typed models.
- Access domain properties (for example, `Patient.nhs_number`) instead of raw dictionary traversal.
- Serialize models back to canonical FHIR JSON with aliases preserved.

## Example usage

The example below shows how to load a simple FHIR R4 Patient payload and obtain the GP ODS code.

```python
from fhir.r4 import Patient

payload = {
 "resourceType": "Patient",
 "identifier": [
  {
   "system": "https://fhir.nhs.uk/Id/nhs-number",
   "value": "9000000009",
  }
 ],
 "generalPractitioner": [
  {
   "type": "Organization",
   "identifier": {
    "system": "https://fhir.nhs.uk/Id/ods-organization-code",
    "value": "A12345",
   },
  }
 ],
}

patient = Patient.model_validate(payload)

nhs_number = patient.nhs_number
gp_ods_code = patient.gp_ods_code

print(nhs_number)   # 9000000009
print(gp_ods_code)  # A12345
```

If `generalPractitioner` is missing, `patient.gp_ods_code` returns `None`.
