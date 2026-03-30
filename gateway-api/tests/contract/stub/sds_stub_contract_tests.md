# SDS Stub Contract Test Documentation

## Overview

The file `test_sds_stub_contract.py` contains contract tests for the
`SdsFhirApiStub` class. This stub is an in-memory implementation of the Spine
Directory Service (SDS) FHIR R4 API used during local and integration testing.
Its purpose is to stand in for the real SDS service without requiring a live
network connection.

The contract tests verify that the stub faithfully reproduces the HTTP behaviour
described in the SDS OpenAPI specification at
<https://github.com/NHSDigital/spine-directory-service-api>. The tests call the
stub's methods directly (no HTTP server is started) and inspect the returned
`requests.Response` objects.

---

## Module-Level Constants

At the top of the module, several string constants are defined for use across
all test classes.

### FHIR-Formatted Query Parameter Constants

The SDS API uses FHIR-style parameter encoding where both a system URL and a
value are joined with a pipe character (`|`). Four constants capture the most
frequently used combinations:

- `_ORG_PROVIDER` — The `organization` query parameter value for the seeded
  "PROVIDER" organisation. Constructed by combining the ODS code FHIR system
  URL (`https://fhir.nhs.uk/Id/ods-organization-code`) with the literal string
  `PROVIDER`.

- `_ORG_CONSUMER` — The same construction for the seeded "CONSUMER"
  organisation.

- `_ORG_UNKNOWN` — A syntactically valid organisation parameter whose ODS code
  (`UNKNOWN_ORG_XYZ`) is guaranteed to have no matching records in the stub.

- `_INTERACTION_ID_PARAM` — The `identifier` query parameter value representing
  the GP Connect "Access Record Structured" service interaction. Constructed by
  combining the NHS service interaction ID system URL
  (`https://fhir.nhs.uk/Id/nhsServiceInteractionId`) with the canonical
  interaction identifier
  `urn:nhs:names:services:gpconnect:fhir:operation:gpc.getstructuredrecord-1`.

- `_PARTY_KEY_PROVIDER` — The `identifier` query parameter value for the
  PROVIDER organisation's MHS party key. Constructed by combining the party
  key system URL (`https://fhir.nhs.uk/Id/nhsMhsPartyKey`) with
  `PROVIDER-0000806`.

- `_PARTY_KEY_CONSUMER` — The same construction for the CONSUMER organisation
  using `CONSUMER-0000807`.

- `_VALID_CORRELATION_ID` — A fixed string used as a sample `X-Correlation-Id`
  header value in tests that verify header echo behaviour.

### URL Constants

- `_BASE_DEVICE_URL` — The canonical sandbox URL for the SDS `/Device`
  endpoint.

- `_BASE_ENDPOINT_URL` — The canonical sandbox URL for the SDS `/Endpoint`
  endpoint.

---

## Fixtures

### `stub`

Creates and returns a new `SdsFhirApiStub` instance. The stub constructor
seeds itself with a set of deterministic Device and Endpoint records, so every
test starts with a known, consistent data state. Because the instance is created
fresh for each test, mutations in one test (such as clearing or adding records)
do not affect other tests.

---

## Test Classes

### `TestGetDeviceBundleSuccess`

This class tests the normal ("happy path") behaviour of the `get_device_bundle`
method when all required inputs are present and the queried organisation exists
in the stub's data store.

Every call in this class supplies the `apikey` header and passes `_ORG_PROVIDER`
as the `organization` parameter together with `_INTERACTION_ID_PARAM` as the
`identifier` parameter.

**`test_status_code_is_200`**  
Calls `get_device_bundle` with valid inputs and asserts that the HTTP status
code of the response is 200.

**`test_content_type_is_fhir_json`**  
Asserts that the `Content-Type` response header contains the string
`application/fhir+json`, which is the media type mandated by the FHIR
specification for all FHIR API responses.

**`test_response_body_resource_type_is_bundle`**  
Parses the response body as JSON and asserts that the `resourceType` field
equals `"Bundle"`. The SDS spec requires that search results are wrapped in a
FHIR Bundle.

**`test_response_body_bundle_type_is_searchset`**  
Asserts that `Bundle.type` equals `"searchset"`. This is the mandatory Bundle
type for FHIR search responses.

**`test_response_bundle_total_matches_entry_count`**  
Asserts that `Bundle.total` (an integer in the response body) equals the number
of items in the `Bundle.entry` array. The FHIR spec requires these two values
to be consistent.

**`test_response_bundle_has_at_least_one_entry_for_known_org`**  
Asserts that `Bundle.total` is at least 1. Because the stub is pre-seeded with
a Device for the PROVIDER organisation, a search for that organisation must
return a non-empty result.

**`test_response_bundle_entry_has_full_url`**  
Iterates over every entry in `Bundle.entry` and asserts that each entry has a
non-empty `fullUrl` field. The FHIR spec requires `fullUrl` to be present in
every Bundle entry.

**`test_response_bundle_entry_full_url_contains_device_id`**  
For every entry, reads `entry.resource.id` and asserts that this value appears
as a substring of `entry.fullUrl`. This verifies that the URL is constructed
from the resource's own identifier.

**`test_response_bundle_entry_has_resource`**  
Asserts that every Bundle entry has a `resource` field. This is the FHIR
container that holds the actual Device or Endpoint object.

**`test_response_bundle_entry_has_search_mode_match`**  
Asserts that `entry.search.mode` equals `"match"` for every entry. This is the
value required by FHIR for entries that directly satisfy the search criteria.

**`test_x_correlation_id_echoed_back_when_provided`**  
Passes `X-Correlation-Id: test-correlation-id-12345` in the request headers and
asserts that the same value appears under `X-Correlation-Id` in the response
headers. The SDS spec states that this header must be mirrored back.

**`test_x_correlation_id_absent_when_not_provided`**  
Does not pass `X-Correlation-Id` and asserts that the header is absent from the
response. This prevents the stub from inventing correlation IDs.

**`test_empty_bundle_returned_for_unknown_org`**  
Passes `_ORG_UNKNOWN` as the organisation parameter and asserts that the
response is still 200 (not 404), that `resourceType` is `"Bundle"`, that
`total` is 0, and that `entry` is an empty list. The SDS spec returns an empty
Bundle rather than a 404 when no records match.

**`test_query_with_party_key_returns_matching_device`**  
Passes both `_INTERACTION_ID_PARAM` and `_PARTY_KEY_PROVIDER` as a list in the
`identifier` parameter and asserts that `Bundle.total` is at least 1. This
verifies that the stub correctly handles multi-value identifier queries.

---

### `TestGetDeviceResourceStructure`

This class verifies the internal structure of each `Device` resource returned
inside the Bundle. Every test in this class makes a valid query for the PROVIDER
organisation and then inspects each `entry.resource` object.

**`test_device_resource_type_is_device`**  
Asserts that every resource has `resourceType` equal to `"Device"`.

**`test_device_has_id`**  
Asserts that every resource has a non-empty `id` field.

**`test_device_has_identifier_list`**  
Asserts that `Device.identifier` is a list containing at least one element.

**`test_device_identifier_contains_asid`**  
Searches `Device.identifier` for an entry whose `system` equals the NHS Spine
ASID system URL (`https://fhir.nhs.uk/Id/nhsSpineASID`) and asserts that at
least one such entry exists.

**`test_device_identifier_contains_party_key`**  
Searches `Device.identifier` for an entry whose `system` equals the MHS party
key system URL (`https://fhir.nhs.uk/Id/nhsMhsPartyKey`) and asserts that at
least one such entry exists.

**`test_device_has_owner`**  
Asserts that every Device resource has an `owner` field.

**`test_device_owner_identifier_uses_ods_system`**  
Navigates to `Device.owner.identifier.system` and asserts it equals the ODS
code FHIR system URL (`https://fhir.nhs.uk/Id/ods-organization-code`). This
links the device to its owning organisation.

---

### `TestGetDeviceBundleValidationErrors`

This class tests the stub's input validation for `get_device_bundle`. Each test
deliberately omits or corrupts a required input and asserts that the stub
responds with HTTP 400 and an `OperationOutcome` body.

**`test_missing_apikey_returns_400`**  
Passes an empty headers dictionary (no `apikey`). The SDS API requires this
header; its absence must yield 400.

**`test_missing_organization_returns_400`**  
Omits the `organization` query parameter. This parameter is mandatory for
`/Device` queries.

**`test_missing_identifier_returns_400`**  
Omits the `identifier` query parameter entirely.

**`test_identifier_without_interaction_id_returns_400`**  
Passes only `_PARTY_KEY_PROVIDER` as the `identifier`, omitting the
`nhsServiceInteractionId` component. The stub requires the interaction ID to be
present in the identifier list for Device queries.

**`test_error_response_resource_type_is_operation_outcome`**  
Sends a request with a missing `apikey` header and asserts that the response
body has `resourceType` equal to `"OperationOutcome"`. All FHIR error responses
must use this resource type.

**`test_error_response_has_non_empty_issue_list`**  
Asserts that the `OperationOutcome.issue` field is a list containing at least
one element.

**`test_error_response_issue_has_severity`**  
Asserts that `issue[0]` contains a `severity` field. FHIR requires every issue
to carry a severity.

**`test_error_response_issue_has_code`**  
Asserts that `issue[0]` contains a `code` field. FHIR requires every issue to
carry an issue type code.

**`test_error_response_issue_has_diagnostics`**  
Asserts that `issue[0]` contains a non-empty `diagnostics` field. This free-text
field carries the human-readable error description.

**`test_missing_apikey_echoes_correlation_id`**  
Passes `X-Correlation-Id` without `apikey` and asserts that, even though the
response is 400, the correlation ID is still echoed back in the response
headers.

---

### `TestGetEndpointBundleSuccess`

This class mirrors `TestGetDeviceBundleSuccess` but for the `get_endpoint_bundle`
method. The key difference is that `organization` is optional for Endpoint
queries; the minimum required parameter is `identifier`.

**`test_status_code_is_200`**  
Calls `get_endpoint_bundle` with the `apikey` header and `_INTERACTION_ID_PARAM`
as the identifier and asserts that the status code is 200.

**`test_content_type_is_fhir_json`**  
Verifies `Content-Type: application/fhir+json` in the response.

**`test_response_body_resource_type_is_bundle`**  
Verifies `Bundle` as the top-level resource type.

**`test_response_body_bundle_type_is_searchset`**  
Verifies `Bundle.type` is `"searchset"`.

**`test_response_bundle_total_matches_entry_count`**  
Verifies that `Bundle.total` equals the length of `Bundle.entry`.

**`test_response_bundle_has_entries_for_known_interaction_id`**  
Asserts that querying by the known seeded interaction ID returns at least one
Endpoint entry.

**`test_response_bundle_entry_has_full_url`**  
Asserts every entry has a non-empty `fullUrl`.

**`test_response_bundle_entry_full_url_contains_endpoint_id`**  
Asserts each entry's `fullUrl` contains the corresponding Endpoint resource ID.

**`test_response_bundle_entry_has_resource`**  
Asserts every entry has a `resource` field.

**`test_response_bundle_entry_has_search_mode_match`**  
Asserts `entry.search.mode` equals `"match"` for every entry.

**`test_organization_is_optional_for_endpoint`**  
Makes a valid request with no `organization` parameter and asserts the status
code is 200. This explicitly documents the difference in required parameters
between `/Device` and `/Endpoint`.

**`test_query_with_party_key_returns_matching_endpoint`**  
Passes both `_INTERACTION_ID_PARAM` and `_PARTY_KEY_PROVIDER` as identifiers
and asserts at least one entry is returned.

**`test_x_correlation_id_echoed_back_when_provided`**  
Verifies the correlation ID echo behaviour for Endpoint responses.

**`test_x_correlation_id_absent_when_not_provided`**  
Verifies the correlation ID is absent when not provided.

**`test_empty_bundle_returned_for_unknown_party_key`**  
Queries with a party key that is not in the stub and asserts a 200 response
with `total: 0` and an empty `entry` array.

---

### `TestGetEndpointResourceStructure`

This class inspects the internal structure of each `Endpoint` resource returned
by the stub. All tests query the stub using `_PARTY_KEY_PROVIDER` as the
identifier so that results are limited to the PROVIDER's seeded endpoint.

**`test_endpoint_resource_type_is_endpoint`**  
Asserts every resource has `resourceType` equal to `"Endpoint"`.

**`test_endpoint_has_id`**  
Asserts every resource has a non-empty `id` field.

**`test_endpoint_has_status_active`**  
Asserts `Endpoint.status` equals `"active"`. The SDS spec requires active
endpoints.

**`test_endpoint_has_connection_type`**  
Asserts the `connectionType` field is present.

**`test_endpoint_connection_type_has_system_and_code`**  
Navigates into `connectionType` and asserts both `system` and `code` fields are
present.

**`test_endpoint_has_payload_type`**  
Asserts `Endpoint.payloadType` is a non-empty list.

**`test_endpoint_has_address`**  
Asserts `Endpoint.address` is present and non-empty. This is the actual network
URL of the endpoint.

**`test_endpoint_has_managing_organization`**  
Asserts the `managingOrganization` field is present.

**`test_endpoint_managing_organization_uses_ods_system`**  
Navigates to `Endpoint.managingOrganization.identifier.system` and asserts it
equals the ODS code FHIR system URL.

**`test_endpoint_has_identifier_list`**  
Asserts `Endpoint.identifier` is a non-empty list.

**`test_endpoint_identifier_contains_asid`**  
Searches `Endpoint.identifier` for an entry with the NHS Spine ASID system URL
and asserts it is present.

**`test_endpoint_identifier_contains_party_key`**  
Searches `Endpoint.identifier` for an entry with the MHS party key system URL
and asserts it is present.

---

### `TestGetEndpointBundleValidationErrors`

This class tests the stub's validation for `get_endpoint_bundle` inputs.

**`test_missing_apikey_returns_400`**  
Omits `apikey` and asserts 400.

**`test_missing_identifier_returns_400`**  
Passes empty params (no `identifier`) and asserts 400. For `/Endpoint`, the
`identifier` parameter is the only mandatory query parameter.

**`test_error_response_resource_type_is_operation_outcome`**  
Asserts the error body `resourceType` is `"OperationOutcome"`.

**`test_error_response_has_non_empty_issue_list`**  
Asserts `issue` is a non-empty list.

**`test_error_response_issue_has_severity`**  
Asserts `issue[0].severity` is present.

**`test_error_response_issue_has_code`**  
Asserts `issue[0].code` is present.

**`test_error_response_issue_has_diagnostics`**  
Asserts `issue[0].diagnostics` is a non-empty string.

**`test_missing_apikey_echoes_correlation_id`**  
Passes `X-Correlation-Id` without `apikey` and asserts the correlation ID
appears in the 400 response headers.

---

### `TestGetConvenienceMethod`

This class tests the `get` method, which is a unified entry point that
delegates to either `get_device_bundle` or `get_endpoint_bundle` based on the
URL, and also records all call metadata for later inspection.

**`test_device_url_returns_device_bundle`**  
Calls `get` with `_BASE_DEVICE_URL` (which contains `/Device`) and asserts the
response is a Bundle of Device resources. This verifies the routing logic: when
the URL contains the substring `/Device`, the call is delegated to
`get_device_bundle`.

**`test_endpoint_url_returns_endpoint_bundle`**  
Calls `get` with `_BASE_ENDPOINT_URL` (which contains `/Endpoint`) and asserts
the response is a Bundle of Endpoint resources. This verifies that any URL
containing `/Endpoint` is routed to `get_endpoint_bundle`.

**`test_get_records_last_url`**  
After calling `get`, asserts that `stub.get_url` equals the URL that was passed
in. The stub stores this so test code can later verify what URL was actually
called.

**`test_get_records_last_headers`**  
After calling `get`, asserts that `stub.get_headers` equals the headers
dictionary that was passed in.

**`test_get_records_last_params`**  
After calling `get`, asserts that `stub.get_params` equals the params
dictionary that was passed in.

**`test_get_records_last_timeout`**  
Calls `get` with `timeout=30` and asserts that `stub.get_timeout` equals 30.

**`test_get_device_without_apikey_returns_400`**  
Calls `get` with a device URL but no `apikey` header and asserts the response
is 400. This verifies that validation is not bypassed by the routing layer.

**`test_get_endpoint_without_apikey_returns_400`**  
Calls `get` with an endpoint URL but no `apikey` header and asserts 400.

---

### `TestUpsertOperations`

This class tests the stub's public data-management API: `upsert_device`,
`clear_devices`, `upsert_endpoint`, and `clear_endpoints`. These methods allow
test code to customise the stub's data store.

**`test_upsert_device_is_returned_by_get_device_bundle`**  
First clears all devices with `clear_devices`, then constructs a minimal Device
dictionary with `resourceType: "Device"`, `id: "new-device-123"`, an empty
identifier list, and an owner identifier using the ODS code system. It calls
`upsert_device` with ODS code `"NEWORG"`, the standard interaction ID, no party
key, and this device dictionary. It then queries `get_device_bundle` for
`"NEWORG"` and asserts that `Bundle.total` is 1 and that the single entry has
`id` equal to `"new-device-123"`.

**`test_clear_devices_removes_all_devices`**  
Calls `clear_devices` and then queries for the PROVIDER organisation. Asserts
that `Bundle.total` is 0, confirming that clearing removes all seeded data.

**`test_upsert_endpoint_is_returned_by_get_endpoint_bundle`**  
First clears all endpoints. Constructs a complete Endpoint dictionary with
`resourceType: "Endpoint"`, `id: "new-endpoint-456"`, `status: "active"`, a
`connectionType` using the stub's `CONNECTION_SYSTEM` constant, a `payloadType`
using the stub's `CODING_SYSTEM` constant, an `address` URL, a
`managingOrganization` using the ODS code system, and an `identifier` list
containing the new party key. Calls `upsert_endpoint` with ODS code `"NEWORG"`,
the standard interaction ID, the new party key, and this endpoint dictionary.
Queries `get_endpoint_bundle` by the new party key and asserts `Bundle.total`
is 1 and the entry ID is `"new-endpoint-456"`.

**`test_clear_endpoints_removes_all_endpoints`**  
Calls `clear_endpoints` and then queries using `_PARTY_KEY_PROVIDER`. Asserts
`Bundle.total` is 0.
