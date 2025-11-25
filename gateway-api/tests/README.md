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
> - `HOSTNAME` - defines the hostname that should be used to access the running APIs. This should match the host portion of the URL provided in the `BASE_URL` environment variable above.

### Install Dependencies (if not using Dev container)

Dev container users can skip this - dependencies are pre-installed during container build.

```bash
cd gateway-api
poetry sync
```

### Run All Tests (with Verbose Output)

From the `tests/` directory:

```bash
pytest -v
```

Or from the `gateway-api/` directory:

```bash
poetry run pytest tests/ -v
```

### Run Specific Test Types

```bash
# Run only acceptance tests
pytest acceptance/ -v

# Run only contract tests
pytest contract/ -v

# Run only integration tests
pytest integration/ -v

# Run only schema validation tests
pytest schema/ -v
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

- **Explicit contract documentation** - The pact file is a versioned artifact that documents the API contract
- **Contract evolution tracking** - Git diffs show exactly how API contracts change over time
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
- **`hostname`**: The hostname of the deployed application (from `HOSTNAME` environment variable highlighted above)
- **`client`**: An HTTP client instance for sending requests to the APIs

These fixtures enable tests to run against the deployed API in a consistent manner across acceptance, integration, and contract tests.
