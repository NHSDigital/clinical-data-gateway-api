# Gateway API BDD Acceptance Tests

This directory contains the BDD (Behaviour-Driven Development) acceptance test suite for the gateway API using pytest-bdd.

These tests verify that the API meets business requirements and acceptance criteria from a user's perspective. They serve as living documentation and ensure the system behaves correctly in real-world scenarios.

## Test Structure

- `features/*.feature` - Gherkin feature files describing user-facing behaviour
- `steps/*.py` - Step definitions that implement the Gherkin steps
- `scenarios/*.py` - Test bindings that link scenarios to pytest test functions
- `conftest.py` - pytest fixtures (includes ResponseContext)

## Running Tests

### Install Dependencies (if not using Dev container)

Dev container users can skip this - dependencies are pre-installed during container build.

```bash
cd gateway-api
poetry install --with dev
```

### Run All BDD Tests with Verbose Output

```bash
poetry run pytest tests/acceptance/ -v
```

### Run Specific Feature

```bash
poetry run pytest tests/acceptance/scenarios/test_gateway_api_responses.py -v
```

### Debug Mode (Show All Output)

```bash
poetry run pytest tests/acceptance/ -v -s
```

## BDD Testing with pytest-bdd

BDD tests describe system behaviour from a user's perspective using natural language (Gherkin syntax). These tests interact with the deployed Lambda function via the AWS Lambda Runtime Interface Emulator (RIE) to test end-to-end scenarios.

### How It Works

1. **Feature Files** (`features/*.feature`)
   - Written in Gherkin syntax (Given/When/Then)
   - Describe behaviour in plain English
   - Readable by non-technical stakeholders
   - Are acceptance tests that meet acceptance criteria

2. **Step Definitions** (`steps/*.py`)
   - Python code that implements each Gherkin step
   - Uses the `Client` fixture to interact with the API
   - Contains assertions to verify expected behaviour

3. **Scenario Bindings** (`scenarios/test_*.py`)
   - Link Gherkin scenarios to pytest test functions using `@scenario` decorator
   - Import step definitions to make them available
   - Should be named after the feature file they bind to

4. **pytest Fixtures** (`conftest.py`)
   - `response_context` - Stores HTTP response state between steps
   - Shared fixtures from `tests/conftest.py` (base_url, hostname, client)
