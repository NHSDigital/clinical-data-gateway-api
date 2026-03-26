# PDS Stub Contract Tests – Plain-English Descriptions

This document describes, in plain English, every piece of code in
`test_pds_stub_contract.py`. The intent is to allow a reviewer to
understand the design decisions and the algorithms being checked without
having to read the source code itself.

---

## Background

The PDS FHIR stub (`PdsFhirApiStub`) is an in-memory imitation of the NHS
Personal Demographics Service (PDS) API. It is used in place of the real
remote service during local and integration testing of the gateway. Because
the stub stands in for a real service, it must faithfully replicate that
service's externally visible behaviour — the "contract" — or tests that
rely on it will give false confidence.

These contract tests exercise the stub directly (no HTTP server is started)
and check that each response it produces matches what the PDS OpenAPI
specification says the real service would return.

---

## Module-Level Constants

### `_ETAG_PATTERN`

A compiled regular expression that describes the format the PDS
specification requires for `ETag` header values. The format is
`W/"<non-negative integer>"` — the letter `W`, a forward-slash, a
double-quote, one or more decimal digits, and a closing double-quote.
Tests use this pattern to confirm that an ETag value is structurally
correct without needing to know the exact version number.

### `_KNOWN_NHS_NUMBER`

The string `"9000000009"`, which corresponds to the test patient "Jane
Smith" that is pre-loaded into the stub when it is created. Using a
pre-seeded number guarantees a successful lookup without any extra test
setup.

### `_UNKNOWN_NHS_NUMBER`

The string `"9000000001"`. This is a syntactically valid 10-digit number
that passes the format check (10 decimal digits) but has deliberately not
been inserted into the stub's in-memory store. It is used to trigger a
"patient not found" (404) path.

The `stub` fixture asserts at construction time that this number is genuinely
absent from the store. If a future change pre-seeds this number, the
assertion will fail with a clear message explaining that `_UNKNOWN_NHS_NUMBER`
must be updated to a number that remains absent.

### `_INVALID_NHS_NUMBER`

The string `"ABC123"`. This contains non-digit characters and is far fewer
than 10 digits long. It is used to trigger the "invalid resource identifier"
(400) path that the PDS spec defines for malformed NHS numbers.

### `_VALID_REQUEST_ID`

A freshly generated UUID (version 4) produced at module-load time and
uppercased. It serves as a realistic, spec-compliant `X-Request-ID` header
value for every test that needs a successful header check to pass.

### `_VALID_CORRELATION_ID`

A freshly generated UUID (version 4) produced at module-load time and
uppercased, generated the same way as `_VALID_REQUEST_ID`. It serves as a
realistic `X-Correlation-ID` header value for tests that check the
echo-back behaviour of that optional header.

---

## Fixtures

### `stub`

Creates a fresh instance of `PdsFhirApiStub` with **strict header
validation enabled** (the default). In strict mode the stub enforces the
PDS specification rule that `X-Request-ID` must be present and must be a
valid UUID; any request that violates this rule receives a 400 error.

After construction, the fixture immediately asserts that `_UNKNOWN_NHS_NUMBER`
is not present in the stub's internal patient store. This guard prevents a
silent test breakage if someone later adds that NHS number to the stub's
pre-seeded data; the assertion will fail with a descriptive message
directing the developer to update the constant instead.

A new instance is created for every individual test that uses this fixture,
so tests are completely isolated from each other.

### `relaxed_stub`

Creates a fresh instance of `PdsFhirApiStub` with **strict header
validation disabled**. In relaxed mode the stub accepts any value (or no
value) for `X-Request-ID` and proceeds directly to patient lookup. This
fixture is used specifically to confirm that the strict-mode behaviour is
controlled by that flag and not hard-wired into every code path.

---

## Class `TestGetPatientSuccess` — Happy-Path 200 Responses

All tests in this class call `stub.get_patient()` with `_KNOWN_NHS_NUMBER`
and `_VALID_REQUEST_ID`. Because both the patient record and the header are
valid, every call should produce a successful 200 response. Each test then
examines a different aspect of that response.

### `test_status_code_is_200`

Checks that the HTTP status code on the response is exactly 200. This is
the most basic assertion: if the stub returns any other code for a valid
request, every subsequent success-path test is meaningless.

### `test_content_type_is_fhir_json`

Checks that the `Content-Type` response header contains the string
`application/fhir+json`. The PDS specification mandates this media type for
all responses; any other content type would indicate the stub is
misrepresenting the wire format.

### `test_response_body_resource_type_is_patient`

Parses the JSON body and checks that the top-level `resourceType` field
equals `"Patient"`. In FHIR every resource carries a `resourceType`
discriminator, and for a patient retrieval endpoint the only allowed value
is `"Patient"`.

### `test_response_body_id_matches_requested_nhs_number`

Parses the JSON body and checks that the `id` field equals the NHS number
that was passed in the request. The PDS specification states that the
resource's logical ID is the patient's NHS number; returning a different
value would mean the caller cannot match the response back to their request.

### `test_response_body_has_meta_version_id`

Checks two things about the `meta` block in the response body: first, that
the `meta` key exists at all; second, that `meta.versionId` is a string
(not an integer or absent). The PDS specification requires a `versionId`
so that clients can supply an `If-Match` header when updating a patient
record.

### `test_etag_header_present`

Checks that an `ETag` header is present at all in a successful response.
Without an ETag, callers cannot perform optimistic-lock updates, so its
absence would be a contract violation.

### `test_etag_header_format`

Retrieves the `ETag` header value and tests it against `_ETAG_PATTERN`. This
verifies that the header follows the `W/"<integer>"` shape required by the
PDS specification and the HTTP weak-validator standard (RFC 7232). A value
like `"1"` (without the `W/` prefix) or `W/abc` would fail this check.

### `test_etag_corresponds_to_meta_version_id`

This is the most precise ETag test. It reads `meta.versionId` from the
response body and constructs the expected ETag value by wrapping the version
ID in the canonical `W/"…"` format. It then asserts that the actual `ETag`
header exactly equals that constructed string. This confirms that the body
and the header are internally consistent — they both describe the same
version of the resource.

### `test_x_request_id_echoed_back`

Checks that the response contains an `X-Request-Id` header (note the
lowercase `d` — the spec uses different casing on the way out from the
request header `X-Request-ID`) and that its value is identical to the
`_VALID_REQUEST_ID` that was sent in. The PDS specification requires
mirroring this header so that callers can correlate responses to their
original requests.

### `test_x_correlation_id_echoed_back_when_provided`

Sends a request that includes both `_VALID_REQUEST_ID` and
`_VALID_CORRELATION_ID`. Checks that the response contains
`X-Correlation-Id` (again lowercase `d`) and that its value matches the
string that was sent. The spec says this optional tracing header must be
echoed back whenever it is provided.

### `test_x_correlation_id_absent_when_not_provided`

Sends a request with no `X-Correlation-ID` header and then confirms that
the response does **not** contain `X-Correlation-Id`. This is the negative
counterpart of the previous test: the stub must not invent a correlation ID
out of nowhere.

---

## Class `TestGetPatientNotFound` — 404 Responses

All tests in this class call `stub.get_patient()` with `_UNKNOWN_NHS_NUMBER`
(a valid-format NHS number not in the store) and `_VALID_REQUEST_ID`.

### `test_status_code_is_404`

Checks that the HTTP status code is 404. This is the mandatory response when
a well-formed NHS number is supplied but no matching patient record exists.

### `test_content_type_is_fhir_json`

Same media-type assertion as in the success class: even error responses must
carry `application/fhir+json`.

### `test_response_body_resource_type_is_operation_outcome`

Checks that the JSON body's `resourceType` is `"OperationOutcome"`. The FHIR
standard requires error responses to be expressed as `OperationOutcome`
resources rather than arbitrary JSON objects or plain text.

### `test_operation_outcome_has_issue`

Checks that the body contains an `issue` array and that the array has at
least one entry. An `OperationOutcome` without any issues would be
meaningless as an error descriptor.

### `test_operation_outcome_spine_code_is_resource_not_found`

Navigates into `body["issue"][0]["details"]["coding"][0]` and checks that
the `code` field equals `"RESOURCE_NOT_FOUND"`. The PDS specification
explicitly maps a 404 patient-not-found scenario to this Spine code, so
using any other code would break consumers that branch on the error code to
decide how to recover.

### `test_operation_outcome_coding_system`

Checks that the same `coding` object's `system` field equals
`"https://fhir.nhs.uk/R4/CodeSystem/Spine-ErrorOrWarningCode"`. This URI is
the canonical authority for Spine error codes; without the correct system
URI, a receiver cannot interpret the `code` value reliably.

### `test_operation_outcome_issue_severity_is_error`

Checks that `issue[0].severity` is `"error"`. The FHIR specification defines
a severity scale (`fatal`, `error`, `warning`, `information`); for a failed
retrieval, `"error"` is the appropriate level.

### `test_x_request_id_echoed_back`

Confirms that even in the 404 case the `X-Request-Id` response header is
present and mirrors the sent `_VALID_REQUEST_ID`. The spec requires this on
all responses, not only successes.

---

## Class `TestGetPatientInvalidNhsNumber` — 400 Responses for Bad NHS Numbers

### `test_status_code_is_400` (parametrized)

This single test method is run four times with four different malformed NHS
number strings:

1. `"ABC123"` — contains non-digit characters.
2. `"123"` — only three digits, far too short.
3. `"12345678901"` — eleven digits, one digit too many.
4. `""` — an empty string.

Each run submits the malformed string (with a valid `X-Request-ID` so
header validation does not interfere) and asserts a 400 status. The
parametrization ensures the stub rejects every category of format violation,
not just one particular kind.

### `test_response_body_resource_type_is_operation_outcome`

Uses `_INVALID_NHS_NUMBER` (`"ABC123"`) and checks that the body's
`resourceType` is `"OperationOutcome"`.

### `test_spine_code_is_invalid_resource_id`

Uses `_INVALID_NHS_NUMBER` and drills into the Spine coding to confirm the
error code is `"INVALID_RESOURCE_ID"`. The PDS specification maps invalid
NHS numbers specifically to this code; any other code would mislead callers
about the nature of the problem.

### `test_content_type_is_fhir_json`

Confirms the `Content-Type` header is `application/fhir+json` even for
this 400 error path.

---

## Class `TestGetPatientMissingRequestId` — 400 Responses for Absent Header

### `test_status_code_is_400_when_request_id_absent`

Calls `get_patient()` with `request_id=None` (no `X-Request-ID` supplied)
against the strict-mode stub with a valid NHS number. Checks that the
result is 400. The PDS specification marks `X-Request-ID` as mandatory on
every request; a missing header must always be rejected.

### `test_response_body_resource_type_is_operation_outcome`

Same call as above; checks the body `resourceType` is `"OperationOutcome"`.

### `test_content_type_is_fhir_json`

Same call; checks the `Content-Type` header.

### `test_no_request_id_validation_in_relaxed_mode`

Uses the `relaxed_stub` fixture (strict mode off). Calls `get_patient()`
with no `request_id` and a valid NHS number, then asserts the response is
200. This test verifies the contract between the stub's `strict_headers`
flag and its behaviour: when relaxed mode is active the missing-header rule
must be suspended entirely, allowing the call to proceed to a successful
patient lookup.

---

## Class `TestGetPatientInvalidRequestId` — 400 Responses for Non-UUID Header

### `test_status_code_is_400_when_request_id_not_uuid`

Sends `request_id="not-a-uuid"` (a plain English string, not a UUID) to the
strict-mode stub with a valid NHS number. Checks the result is 400. The PDS
specification requires `X-Request-ID` to be a UUID; sending an arbitrary
string must be rejected.

### `test_response_body_resource_type_is_operation_outcome`

Same call; checks the body `resourceType`.

### `test_content_type_is_fhir_json`

Same call; checks the `Content-Type` header.

### `test_no_request_id_format_validation_in_relaxed_mode`

Uses the `relaxed_stub` fixture. Sends `request_id="not-a-uuid"` with a
valid NHS number. Asserts a 200 response. This confirms that the UUID format
check, like the presence check, is gated behind the `strict_headers` flag
and not applied unconditionally.

---

## Class `TestOperationOutcomeStructure` — Shared Error-Body Shape

This class applies a set of structural assertions to every kind of error
response the stub can produce, ensuring they all share the same FHIR-
conformant shape.

### `error_response` fixture (parametrized)

This is a **fixture defined inside the class**, not a standalone test. It
accepts four scenarios as parameters:

1. **`missing_request_id`** — `request_id=None`, valid NHS number. Triggers
   the missing-header rejection path.
2. **`invalid_request_id`** — `request_id="not-a-uuid"`, valid NHS number.
   Triggers the non-UUID header rejection path.
3. **`invalid_nhs`** — valid request ID, `_INVALID_NHS_NUMBER`. Triggers the
   invalid NHS number path.
4. **`not_found`** — valid request ID, `_UNKNOWN_NHS_NUMBER`. Triggers the
   patient-not-found path.

For each scenario the fixture calls `stub.get_patient()` with the
appropriate arguments and returns the resulting `requests.Response` object.
Every test method in this class that declares `error_response` as a
parameter will be run once for each of these four scenarios, giving
4 × 7 = 28 test executions in total.

### `test_resource_type`

For every error scenario: parses the body and asserts `resourceType` equals
`"OperationOutcome"`.

### `test_issue_array_is_present_and_non_empty`

For every error scenario: asserts that the `issue` key exists, that its
value is a list, and that the list contains at least one entry.

### `test_issue_has_severity`

For every error scenario: asserts that the first item in the `issue` array
has a `severity` field. Does not constrain the value; that is checked in
more specific tests.

### `test_issue_has_code`

For every error scenario: asserts that the first `issue` item has a `code`
field. The FHIR `OperationOutcome.issue.code` is a required element that
categorises the kind of problem (e.g. `"value"`, `"structure"`).

### `test_issue_details_coding_system`

For every error scenario: drills down into `issue[0].details.coding[0]` and
asserts that the `system` field equals the Spine error code system URI
(`"https://fhir.nhs.uk/R4/CodeSystem/Spine-ErrorOrWarningCode"`). This
ensures all error responses use a consistent, spec-mandated vocabulary
namespace.

### `test_issue_details_coding_has_code`

For every error scenario: asserts that the same `coding` object has a `code`
field and that the field is non-empty (truthy). This confirms that every
error carries a machine-readable Spine code that callers can act on.

### `test_issue_details_coding_has_display`

For every error scenario: asserts that the `coding` object has a `display`
field and that it is non-empty. The `display` is a human-readable label for
the error code; its presence makes the response useful for logging and
debugging without requiring the caller to look up the code separately.

---

## Class `TestGetConvenienceMethod` — The `get()` HTTP-Style Wrapper

The stub also exposes a `get(url, headers, …)` method that mimics the
interface of `requests.get()`. Internally it parses the NHS number from the
tail of the URL path and extracts named headers from the dictionary, then
delegates to `get_patient()`. These tests confirm that delegation works
correctly.

### `test_get_known_patient_returns_200`

Constructs a realistic PDS URL whose path ends in the known NHS number
(`9000000009`) and passes a headers dictionary containing only
`X-Request-ID`. Asserts the response is 200. This confirms that the NHS
number extraction from the URL and the header extraction from the dictionary
both work for the happy path.

### `test_get_without_request_id_returns_400`

Constructs the same URL but passes an empty headers dictionary (no
`X-Request-ID`). Asserts the response is 400. This confirms that header
extraction correctly produces `None` when the key is absent, which then
triggers the strict-mode header rejection in `get_patient()`.

### `test_get_passes_correlation_id`

Constructs the same URL and passes both `X-Request-ID` and
`X-Correlation-ID` in the headers dictionary. Asserts that the response
header `X-Correlation-Id` equals `_VALID_CORRELATION_ID`. This confirms
that the `get()` wrapper correctly forwards the optional correlation ID
through to `get_patient()` and that `get_patient()` in turn echoes it back
in the response.
