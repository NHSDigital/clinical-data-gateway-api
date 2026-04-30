# Gateway API

## Testing

The Gateway API has five types of tests, each serving a different purpose:

- **[Unit, Contract, Schema, & Integration Tests](tests/README.md)** — Developer-focused technical tests using pytest
- **[BDD Acceptance Tests](tests/acceptance/features/README.md)** — Business-focused assurance tests using pytest-bdd

### Continuous Integration

All test types (unit, contract, schema, integration, and acceptance) run automatically in the CI/CD pipeline on every push and pull request. **Any test failure at any level will cause the pipeline to fail and prevent the PR from being merged.**

Additionally, code coverage is collected from all test types, merged, and analyzed by SonarCloud. PRs must meet minimum coverage thresholds to pass quality gates.

### Quick Test Commands

```bash
# From the root directory, run all tests (unit, contract, schema, integration, acceptance)
make test

# Run specific test suites
make test-acceptance       # BDD acceptance tests (pytest-bdd)
make test-contract         # Contract tests (Pact)
make test-integration      # Integration tests
make test-schema           # Schema validation tests (Schemathesis)

# Unit tests are co-located with source code under src/
make test-unit
```

For detailed testing documentation, see the README files in each test directory.

## Project Structure

```text
gateway-api/
├── openapi.yaml                           # OpenAPI 3.0 specification
├── pyproject.toml                         # Poetry dependencies, build config, and tool settings
├── poetry.lock                            # Locked dependency versions
├── README.md
├── src/
│   ├── fhir/                              # FHIR data model classes (Bundle, Patient, etc.)
│   │   ├── bundle.py
│   │   ├── general_practitioner.py
│   │   ├── human_name.py
│   │   ├── identifier.py
│   │   ├── operation_outcome.py
│   │   ├── parameters.py
│   │   ├── patient.py
│   │   └── period.py
│   └── gateway_api/                       # Flask application and business logic
│       ├── app.py                         # Flask app, routes, and entry point
│       ├── controller.py                  # Orchestrates PDS → SDS → GP provider calls
│       ├── common/                        # Shared types, helpers, and error definitions
│       │   ├── common.py                  # FlaskResponse, NHS number validation, etc.
│       │   └── error.py                   # Error classes (AbstractCDGError and subclasses)
│       ├── clinical_jwt/                  # Clinical JWT handling
│       ├── get_structured_record/         # Request parsing for $gpc.getstructuredrecord
│       │   └── request.py                 # GetStructuredRecordRequest class
│       ├── pds/                           # PDS FHIR API client (patient demographics)
│       │   ├── client.py                  # PdsClient — looks up patient GP practice
│       │   └── search_results.py          # PdsSearchResults data class
│       ├── sds/                           # SDS FHIR API client (Spine Directory Service)
│       │   ├── client.py                  # SdsClient — retrieves ASIDs and endpoints
│       │   └── search_results.py          # SdsSearchResults data class
│       └── provider/                      # GP provider FHIR client
│           └── client.py                  # GpProviderClient — fetches structured records
├── stubs/
│   └── stubs/                             # API stubs used for local and test environments
│       ├── base_stub.py                   # Base class for building stub responses
│       ├── pds/                           # PDS FHIR API stub
│       │   └── stub.py
│       ├── sds/                           # SDS FHIR API stub
│       │   └── stub.py
│       ├── provider/                      # GP provider stub
│       │   └── stub.py
│       └── data/                          # Fixture data returned by stubs
│           ├── bundles/                   # FHIR Bundle fixtures
│           └── patients/                  # Patient record fixtures
├── tests/
│   ├── conftest.py                        # Shared pytest fixtures
│   ├── acceptance/                        # BDD acceptance tests (pytest-bdd)
│   │   ├── conftest.py
│   │   ├── features/                      # Gherkin .feature files
│   │   │   └── happy_path.feature
│   │   ├── scenarios/                     # Scenario-to-test bindings
│   │   │   └── test_happy_path.py
│   │   └── steps/                         # Step definitions
│   │       └── happy_path.py
│   ├── contract/                          # Contract tests (Pact)
│   │   ├── test_consumer_contract.py
│   │   ├── test_provider_contract.py
│   │   └── pacts/                         # Generated Pact JSON files
│   ├── integration/                       # Integration tests (against running container)
│   │   ├── test_get_structured_record.py
│   │   └── test_sds_search.py
│   ├── schema/                            # Schema validation tests (Schemathesis)
│   │   └── test_openapi_schema.py
│   ├── data/                              # Shared test fixture data
│   │   ├── gpc_bundle/
│   │   └── patient/
│   └── manual-test/                       # Manual / exploratory test helpers
│       └── api-test/
└── test-artefacts/                        # CI-generated test reports and coverage files
```

> **Note:** Unit tests are co-located alongside the source files they test (e.g. `src/gateway_api/test_app.py` tests `src/gateway_api/app.py`). This keeps tests close to the code they exercise.

## Dependencies

### Runtime Dependencies

Specified under `[tool.poetry.dependencies]` in `pyproject.toml`:

| Package | Description |
| --- | --- |
| `flask` | Web framework powering the Gateway API |
| `requests` | HTTP client for calling PDS, SDS, and GP provider APIs |
| `types-flask` | Type stubs for Flask (used by mypy) |

### Dev Dependencies

Specified under `[dependency-groups] dev` in `pyproject.toml`:

| Package | Description |
| --- | --- |
| `mypy` | Static type checker (strict mode enabled) |
| `pytest` | Test runner |
| `pytest-bdd` | BDD-style acceptance tests with Gherkin feature files |
| `pytest-cov` | Coverage measurement for pytest |
| `pytest-html` | HTML test report generation |
| `pytest-mock` | Mock/patch helpers for pytest |
| `pact-python` | Consumer-driven contract testing |
| `python-dotenv` | Loads `.env` files into environment variables |
| `schemathesis` | Property-based testing of OpenAPI schemas |
| `types-requests` | Type stubs for the `requests` library |
| `types-pyyaml` | Type stubs for PyYAML |
