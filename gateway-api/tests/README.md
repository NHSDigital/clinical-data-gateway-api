# Gateway API Tests

This directory contains the acceptance, contract, integration, and schema validation test suites for the gateway API.

## Test Structure

```text
tests/
├── conftest.py                          # Shared pytest fixtures (includes base_url, hostname, client)
├── acceptance/                          # Acceptance tests (BDD with pytest-bdd)
│   ├── conftest.py                      # Acceptance test fixtures (ResponseContext)
│   ├── scenarios/test_*.py              # Scenario bindings, should be named after the feature file the python script is providing scenario bindings for
│   ├── features/                        # Gherkin feature files
│   └── steps/                           # Step definitions
├── contract/                            # Contract tests (Pact)
│   ├── test_consumer_contract.py        # Consumer contract definitions
│   ├── test_provider_contract.py        # Provider contract verification
│   └── pacts/                           # Generated pact files
│       └── GatewayAPIConsumer-GatewayAPIProvider.json
├── integration/                         # Integration tests
└── schema/                              # Schema validation tests
    └── test_openapi_schema.py           # Schemathesis property-based tests
```

## Running Tests
>
> [!NOTE]<br>
> When running tests the following environment variables need to be provided:
>
> - `BASE_URL` - defines the protocol, hostname and port that should used to access the running APIs. Should be included as a URL in the format <protocol>:<hostname>:<port>, for example "<http://localhost:5000>" if the APIs are available on the "localhost" host via HTTP using port 5000.
> - `HOST` - defines the hostname that should be used to access the running APIs. This should match the host portion of the URL provided in the `BASE_URL` environment variable above.

### Install Dependencies (if not using Dev container)

Dev container users can skip this - dependencies are pre-installed during container build.

```bash
cd gateway-api
poetry sync
```

### Run All Tests (with Verbose Output)

From the root of the repository:

```bash
pytest -v
```

### Run Specific Test Types

```bash
# Run only acceptance tests
pytest gateway-api/tests/acceptance/ -v

# Run only contract tests
pytest gateway-api/tests/contract/ -v

# Run only integration tests
pytest gateway-api/tests/integration/ -v

# Run only schema validation tests
pytest gateway-api/tests/schema/ -v
```

## Test Types

### Acceptance Tests (`acceptance/`)

Behavior-driven development (BDD) tests using pytest-bdd and Gherkin syntax. These tests validate the API from an end-user perspective.

**Structure:**

- **Feature files** (`features/*.feature`): Written in Gherkin, these define scenarios in plain language
- **Step definitions** (`steps/*.py`): Python implementations that map Gherkin steps to actual test code
- **Test bindings** (`scenarios/test_*.py`): Link scenarios to pytest test functions using `@scenario` decorator

**How it works:**

1. Feature files describe behavior in Given/When/Then format
2. Step definitions provide the Python implementation for each step
3. Test files create pytest test functions that bind to specific scenarios
4. Tests run against the deployed API using the `base_url` fixture from `conftest.py`
5. Pytest is configured to find the features within the `acceptance` directory via the `bdd_features_base_dir` parameter within the `pytest.ini` file

**Example workflow:**

```gherkin
Scenario: Get hello world message
  Given the API is running
  When I send "World" to the endpoint
  Then the response status code should be 200
  And the response should contain "Hello, World!"
```

The steps are implemented in `steps/hello_world_steps.py` and bound in `test_hello_world.py`.

### Integration Tests (`integration/`)

Integration tests that validate the APIs behavior through HTTP requests. These tests use a `Client` fixture that sends requests to the deployed Lambda function via the AWS Lambda Runtime Interface Emulator (RIE).

**How it works:**

- Tests use the `Client` class from `conftest.py` to interact with the API
- The client sends HTTP POST requests to the APIs
- Tests verify response status codes, headers, and response bodies
- Tests validate both successful requests and error handling

**Example test cases:**

- Successful "hello world" responses
- Error handling for missing or empty payloads
- Error handling for non-existent resources
- Content-Type header validation

**Key difference from acceptance tests:**

- Integration tests use direct pytest assertions without Gherkin syntax
- More focused on testing specific API behaviors and edge cases
- Uses the same `Client` fixture as acceptance tests but with standard pytest structure

### Schema Validation Tests (`schema/`)

Property-based API schema validation tests using Schemathesis. These tests automatically generate test cases from the OpenAPI specification (`openapi.yaml`) and validate that the API implementation matches the schema.

**How it works:**

- Loads the OpenAPI schema from `openapi.yaml`
- Uses the `base_url` fixture to test against the running API
- Automatically generates test cases including:
  - Valid inputs
  - Edge cases
  - Boundary values
  - Invalid inputs
- Validates that responses match the schema definitions

### Contract Testing with Pact (`contract/`)

Contract testing ensures that the consumer's expectations match the provider's implementation without requiring both systems to be tested together.

**How it works:**

1. **Consumer Tests** (`test_consumer_contract.py`):
   - Define what the consumer EXPECTS from the API
   - Test against a **mock Pact server** (not the real API)
   - The mock server responds based on the defined expectations
   - Generates a pact contract file (`GatewayAPIConsumer-GatewayAPIProvider.json`) with all interactions
   - **Key point:** These tests don't call the real API

2. **Provider Integration Tests** (`test_provider_contract.py`):
   - Verify the **actual deployed API** implementation
   - Read the pact contract file generated by consumer tests
   - Verify that the real API implementation satisfies the consumer's expectations
   - **Key point:** This is where the real API gets tested

**The Flow:**

```text
Consumer Test → Mock Pact Server → Contract File (JSON)
                                         ↓
                                 Provider Test ← Real Deployed API
```

**Why this approach as opposed to a standard integration test?**

- **Explicit contract documentation** - The pact file is a versioned artefact that documents the API contract
- **Contract evolution tracking** - Because of the above - Git diffs will show exactly how API contracts change over time

- **Consumer-driven development** - Consumers define their needs; providers verify they meet them
- **Prevents breaking changes** - Provider tests fail if changes break existing consumer expectations

### Contract Testing Workflow

**Important:** When modifying consumer expectations, consumer tests must run before provider tests to regenerate the contract file. Since the pact file is committed to version control, provider tests can typically run independently using the existing contract file.

## Pact Files

Consumer tests generate the pact contract files in `tests/contract/pacts/` (e.g., `GatewayAPIConsumer-GatewayAPIProvider.json`).

**Key points:**

- The pact contract file represents the contract between the consumer and provider
- This file is committed to version control so you can track contract changes through git diffs
- The `pact.write_file()` call merges interactions (updates existing or adds new ones)
- Interactions with the same description get replaced; different descriptions get added

## Shared Fixtures

Shared fixtures in `tests/conftest.py` are available across all test types:

- **`base_url`**: The base URL of the deployed Lambda function (from `BASE_URL` environment variable highlighted above)
- **`host`**: The hostname of the deployed application (from `HOST` environment variable highlighted above)
- **`client`**: An HTTP client instance for sending requests to the APIs

## Test Reports

Test execution generates multiple report formats for both local development and CI/CD pipelines:

### JUnit XML Reports

JUnit XML format is used for CI/CD integration and test result summaries. All reports are displayed in GitHub Actions UI using `test-summary/action`.

**All Test Types (Unit, Contract, Schema, Integration, Acceptance):**

- Generated with `--junit-xml=test-artefacts/{type}-tests.xml`
- Contains test results, execution times, and failure details

### HTML Test Reports

Human-readable HTML reports for detailed test analysis:

**Tests using pytest (Unit, Contract, Schema, Integration, Acceptance):**

- Generated with `--html=test-artefacts/{type}-tests.html --self-contained-html`
- Self-contained HTML files with embedded CSS/JavaScript
- Include:
  - Test results with pass/fail status
  - Execution times
  - Test metadata

### CI/CD Report Artefacts

In GitHub Actions, test reports are:

1. **Uploaded as artefacts** - Available for 30 days via workflow run page
2. **Published to job summary** - Displayed in the Actions UI using `test-summary/action`
3. **Attached to pull requests** - Test results appear in PR checks

All reports are stored in `gateway-api/test-artefacts/` and uploaded with artefact names like `unit-test-results`, `contract-test-results`, etc.

## Code Coverage

Code coverage is collected from all four test types (unit, contract, schema, and integration), merged into a unified code coverage report, sent to SonarCloud, which enforces the minimum coverage percentage threshold.

### Coverage Collection per Test Type

Each test execution script (`scripts/tests/*.sh`) collects coverage data independently:

**Unit, Contract, Schema, Integration, and Acceptance Tests** (pytest-based):

- Use `pytest-cov` plugin with `--cov=src/gateway_api` flag
- Generate individual coverage data files: `.coverage`
- Each test type saves its coverage file as `coverage.{type}` (e.g., `coverage.unit`, `coverage.contract`, `coverage.schema`)
- Produce HTML reports for local viewing and terminal output for CI logs

### CI/CD Coverage Workflow

The GitHub Actions workflow (`.github/workflows/stage-2-test.yaml`) orchestrates coverage collection:

```text
              ┌───────────────────────┐
              │create-coverage-name   │
              │                       │
              │ Generate unique name: │
              │ coverage-{branch}-    │
              │ {run_number}.xml      │
              └───────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  Parallel Test Execution (5 jobs)                                        │
├─────────────┬──────────────┬──────────────┬─────────────────┬────────────┤
│  test-unit  │test-contract │ test-schema  │test-integration │test-accept │
│             │              │              │                 │            │
│ Saves:      │ Saves:       │ Saves:       │ Saves:          │ Saves:     │
│ coverage.   │ coverage.    │ coverage.    │ coverage.       │ coverage.  │
│   unit      │   contract   │   schema     │   integration   │  acceptance│
└─────┬───────┴──────┬───────┴──────┬───────┴────────┬────────┴─────┬──────┘
      │              │              │                │              │
      └──────────────┴──────────────┴────────────────┴──────────────┘
                          ↓
              ┌───────────────────────┐
              │ merge-test-coverage   │
              │                       │
              │ 1. Download all 5     │
              │    coverage files     │
              │ 2. Combine into one   │
              │ 3. Generate XML       │
              │ 4. Fix paths with sed │
              │ 5. Rename with unique │
              │    name from job 1    │
              │ 6. Upload merged XML  │
              └───────────┬───────────┘
                          ↓
              ┌───────────────────────┐
              │ sonarcloud-analysis   │
              │                       │
              │ 1. Download merged    │
              │    coverage XML       │
              │ 2. Send to SonarCloud │
              │ 3. Enforce thresholds │
              └───────────────────────┘
```
